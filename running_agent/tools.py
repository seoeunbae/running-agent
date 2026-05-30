"""Tool implementations for the Running Planner Agent."""

import asyncio
import json
import os
import urllib.parse
import urllib.request

from google.adk.tools import ToolContext
from google.genai import types
from google import genai


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _generate_with_retry(client, model, contents, config, max_retries=3, backoff=2):
    for attempt in range(1, max_retries + 1):
        try:
            return await client.aio.models.generate_content(
                model=model, contents=contents, config=config
            )
        except Exception as e:
            if ("429" in str(e) or "ResourceExhausted" in str(e)) and attempt < max_retries:
                await asyncio.sleep(backoff ** attempt)
            else:
                raise


def _zoom_for_diff(diff: float) -> int:
    if diff < 0.001:
        return 16
    if diff < 0.003:
        return 15
    if diff < 0.008:
        return 14
    if diff < 0.02:
        return 13
    if diff < 0.05:
        return 12
    return 11


# ---------------------------------------------------------------------------
# Tool: weather
# ---------------------------------------------------------------------------

def get_weather_forecast(location: str, date: str) -> dict:
    """러닝 당일의 날씨 예보를 조회합니다.

    [중요] 러닝 계획 수립 시 가장 먼저 호출해야 합니다.
    강수·기온·바람 조건이 러닝 안전과 컨디션에 직접 영향을 미치므로,
    날씨를 먼저 확인하여 러닝 가능 여부와 일정을 확정하세요.
    """
    if "이번 주말" in date:
        return {
            "location": location,
            "date": date,
            "rain_probability": 0.70,
            "forecast": "강수 확률 70% (비 예보 발생)",
            "temperature": "18°C",
            "running_condition": "러닝 비권장 — 미끄럼 및 저체온 위험",
        }
    return {
        "location": location,
        "date": date,
        "rain_probability": 0.10,
        "forecast": "맑음, 최고 기온 24°C",
        "temperature": "24°C",
        "running_condition": "러닝 최적 조건",
    }


# ---------------------------------------------------------------------------
# Tool: route-planner
# ---------------------------------------------------------------------------

def get_route_elevation(location: str, distance: str, max_elevation_gain: str) -> dict:
    """러닝 코스의 경로와 고도 정보를 조회합니다.

    날씨 확정 후 두 번째 단계로 호출합니다.
    사용자 체력 수준에 맞는 최적 러닝 코스를 선정하기 위해 사용합니다.
    """
    return {
        "route_name": f"{location} 추천 러닝 코스 A",
        "start": f"{location} 출발 지점",
        "destination": f"{location} 도착 지점",
        "distance": distance,
        "elevation_gain": "35m",
        "max_elevation_gain_allowed": max_elevation_gain,
        "surface": "포장도로 + 흙길 혼합",
        "difficulty": "초중급",
    }


# ---------------------------------------------------------------------------
# Tool: facility-finder
# ---------------------------------------------------------------------------

def search_nearby_facilities(location: str, type: str, radius_km: int = 3) -> dict:
    """러닝 코스 주변의 편의 시설을 검색합니다.

    코스 확정 후 세 번째 단계로 호출합니다.
    출발·도착 지점 근처의 편의점, 카페, 공중화장실, 샤워 시설 등
    러너에게 필요한 시설을 탐색합니다.
    """
    return {
        "location": location,
        "type": type,
        "radius_km": radius_km,
        "facilities": [
            {"name": f"{location} GS25 편의점", "distance": "0.3km", "note": "에너지바·이온음료 구비"},
            {"name": f"{location} 카페 런너스", "distance": "0.8km", "note": "러너 전용 라커 및 샤워실 운영"},
            {"name": f"{location} 공중화장실", "distance": "0.2km", "note": "24시간 개방"},
        ],
        "status": "SUCCESS",
    }


# ---------------------------------------------------------------------------
# Tool: map-visualizer
# ---------------------------------------------------------------------------

async def search_running_course(
    tool_context: ToolContext, location: str, distance_km: float = 5.0
) -> str:
    """Google Maps를 활용해 주변 러닝 코스를 탐색하고 지도 이미지를 생성합니다.

    편의 시설 확인 후 네 번째(마지막) 단계로 호출합니다.
    실제 Google Maps 데이터 기반으로 공원·하천변·트레일 등 러닝에 적합한 장소를 찾아
    경로를 시각화한 지도 이미지를 생성합니다.

    Args:
        tool_context: The context of the tool call.
        location: 러닝 시작 위치 (예: "한강공원", "서울숲", "남산").
        distance_km: 희망 러닝 거리 km (기본값: 5.0).

    Returns:
        러닝 코스 추천 정보와 지도 이미지 생성 결과.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    client = genai.Client()

    search_prompt = (
        f"'{location}' 주변에서 러닝하기 좋은 공원, 하천변 산책로, 트레일을 검색해주세요. "
        f"목표 거리는 약 {distance_km}km입니다. "
        f"각 장소의 이름, 특징, 예상 거리, 난이도를 한국어로 알려주세요."
    )

    search_text = ""
    course_place_id = None

    try:
        resp = await _generate_with_retry(
            client,
            model="gemini-2.5-flash",
            contents=search_prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_maps=types.GoogleMaps())]
            ),
        )
        search_text = resp.text

        if resp.candidates and resp.candidates[0].grounding_metadata:
            for chunk in resp.candidates[0].grounding_metadata.grounding_chunks or []:
                if hasattr(chunk, "maps") and chunk.maps and chunk.maps.place_id:
                    pid = chunk.maps.place_id
                    course_place_id = pid.replace("places/", "") if pid.startswith("places/") else pid
                    break
    except Exception as e:
        search_text = f"Google Maps 러닝 코스 검색 중 오류가 발생했습니다: {e}"

    fallback_url = (
        f"https://www.google.com/maps/search/?api=1"
        f"&query={urllib.parse.quote(location + ' 러닝코스')}"
    )

    if not api_key:
        return f"{search_text}\n\n**지도 보기:** [Google Maps에서 러닝 코스 확인하기]({fallback_url})"

    # Resolve start coordinates
    start_coords = _geocode(location, api_key)
    if not start_coords:
        return f"{search_text}\n\n**지도 보기:** [Google Maps에서 러닝 코스 확인하기]({fallback_url})"

    # Resolve end coordinates
    end_coords = _place_coords(course_place_id, api_key) if course_place_id else None
    if not end_coords or end_coords == start_coords:
        lat0, lng0 = map(float, start_coords.split(","))
        offset = (distance_km / 2) / 111.0
        end_coords = f"{lat0 + offset},{lng0}"

    polyline = _compute_walking_polyline(start_coords, end_coords, api_key)

    map_url = _build_static_map_url(start_coords, end_coords, polyline, api_key)
    directions_url = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&origin={urllib.parse.quote(start_coords)}"
        f"&destination={urllib.parse.quote(end_coords)}"
        f"&travelmode=walking"
    )

    try:
        req = urllib.request.Request(map_url, headers={"User-Agent": "Mozilla/5.0"})
        img_bytes = urllib.request.urlopen(req).read()
        filename = f"running_course_{location}.png"
        artifact = types.Part(inline_data=types.Blob(data=img_bytes, mime_type="image/png"))
        version = await tool_context.save_artifact(filename=filename, artifact=artifact)
        return (
            f"러닝 코스 지도 이미지가 artifact `{filename}` (version {version})으로 저장되었습니다.\n\n{search_text}\n\n"
            f"**지도 보기:** [Google Maps에서 경로 확인하기]({directions_url})"
        )
    except Exception as e:
        return (
            f"지도 이미지 생성 중 오류: {e}\n\n{search_text}\n\n"
            f"**지도 보기:** [Google Maps에서 경로 확인하기]({directions_url})"
        )


def _geocode(location: str, api_key: str) -> str | None:
    try:
        q = urllib.parse.quote(location)
        url = (
            f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            f"?input={q}&inputtype=textquery&fields=geometry&key={api_key}"
        )
        data = json.loads(urllib.request.urlopen(url).read().decode())
        if data.get("status") == "OK" and data.get("candidates"):
            loc = data["candidates"][0]["geometry"]["location"]
            return f"{loc['lat']},{loc['lng']}"
    except Exception:
        pass
    return None


def _place_coords(place_id: str, api_key: str) -> str | None:
    try:
        url = (
            f"https://maps.googleapis.com/maps/api/place/details/json"
            f"?place_id={place_id}&fields=geometry&key={api_key}"
        )
        data = json.loads(urllib.request.urlopen(url).read().decode())
        if data.get("status") == "OK":
            loc = data["result"]["geometry"]["location"]
            return f"{loc['lat']},{loc['lng']}"
    except Exception:
        pass
    return None


def _compute_walking_polyline(start: str, end: str, api_key: str) -> str:
    try:
        lat1, lng1 = map(float, start.split(","))
        lat2, lng2 = map(float, end.split(","))
        payload = {
            "origin": {"location": {"latLng": {"latitude": lat1, "longitude": lng1}}},
            "destination": {"location": {"latLng": {"latitude": lat2, "longitude": lng2}}},
            "travelMode": "WALK",
            "languageCode": "ko",
        }
        req = urllib.request.Request(
            "https://routes.googleapis.com/directions/v2:computeRoutes",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": "routes.polyline.encodedPolyline",
            },
            method="POST",
        )
        data = json.loads(urllib.request.urlopen(req).read().decode())
        if data.get("routes"):
            return data["routes"][0]["polyline"]["encodedPolyline"]
    except Exception:
        pass
    return ""


def _build_static_map_url(start: str, end: str, polyline: str, api_key: str) -> str:
    lat_s, lng_s = map(float, start.split(","))
    lat_e, lng_e = map(float, end.split(","))
    center = f"{(lat_s + lat_e) / 2},{(lng_s + lng_e) / 2}"
    zoom = _zoom_for_diff(max(abs(lat_s - lat_e), abs(lng_s - lng_e)))

    base = (
        f"https://maps.googleapis.com/maps/api/staticmap?size=500x500"
        f"&markers=color:green%7Clabel:S%7C{start}"
        f"&markers=color:red%7Clabel:E%7C{end}"
        f"&center={center}&zoom={zoom}&key={api_key}"
    )
    if polyline:
        return base + f"&path=color:0xFF4500%7Cweight:5%7Cenc:{urllib.parse.quote(polyline)}"
    return base


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

def get_tools() -> list:
    return [
        get_weather_forecast,
        get_route_elevation,
        search_nearby_facilities,
        search_running_course,
    ]
