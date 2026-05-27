from google.adk import Agent

# ==========================================
# 1. ADK Tools Definition (Priority Docstrings)
# ==========================================

def get_weather_forecast(location: str, date: str) -> dict:
    """일기 예보 정보를 실시간으로 조회합니다.
    
    [중요] 야외 레저 활동(라이딩, 캠핑 등) 계획을 수립할 때, 
    날씨 조건에 따라 전체 일정 자체가 연기되거나 변동될 수 있으므로, 
    반드시 가장 먼저 호출하여 날짜를 확정해야 합니다.
    """
    # 이번 주말 기상 악화 시뮬레이션
    if "이번 주말" in date:
        return {
            "location": location,
            "date": date,
            "rain_probability": 0.70,
            "forecast": "강수 확률 70% (비 예보 발생)",
            "temperature": "18°C"
        }
    # 다음 주말 화창한 기상 시뮬레이션
    return {
        "location": location,
        "date": date,
        "rain_probability": 0.10,
        "forecast": "맑음, 최고 기온 24°C",
        "temperature": "24°C"
    }


def get_route_elevation(location: str, distance: str, max_elevation_gain: str) -> dict:
    """특정 지역의 자전거/러닝 코스 경로와 고도 상승 정보를 조회합니다.
    
    날씨와 일정이 최종 확정된 이후, 조건에 맞는 최적의 코스(메인 액티비티)를 
    선택하기 위해 두 번째 단계로 호출해야 합니다.
    """
    return {
        "route_name": "A 코스 (북한강 자전거길)",
        "start": "가평역",
        "destination": "자라섬 캠핑 입구",
        "distance": "10.2km",
        "elevation_gain": "35m",
        "max_elevation_gain_allowed": max_elevation_gain
    }


def search_nearby_facilities(location: str, type: str, radius_km: int = 5) -> dict:
    """특정 좌표 또는 지점 주변의 연계 편의 시설을 검색합니다.
    
    일정과 메인 코스가 확정된 후, 도착지점 혹은 출발지점 근처의 캠핑장, 
    식당 등을 연계 탐색하기 위해 세 번째 단계로 호출해야 합니다.
    """
    # 도착지 주변의 가용 캠핑장이 없는 상황 시뮬레이션 (폴백 트리거)
    if "자라섬" in location:
        return {
            "location": location,
            "type": type,
            "radius_km": radius_km,
            "facilities": [],
            "status": "NO_RESULTS_FOUND",
            "message": "도착점 주변 5km 이내에 예약 가능한 캠핑장이 없습니다."
        }
    
    # 출발지(가평역) 주변 대체 캠핑장 리스트 반환 (폴백 응답)
    return {
        "location": location,
        "type": type,
        "radius_km": radius_km,
        "facilities": [
            {"name": "가평 푸른숲 글램핑", "distance": "3.2km"},
            {"name": "역전 숲속 쉼터", "distance": "1.5km"}
        ],
        "status": "SUCCESS"
    }


# ==========================================
# 2. ADK Agent Definition & Orchestration Rules
# ==========================================

root_agent = Agent(
    name="LeisurePlanner",
    model="gemini-2.5-flash",
    instruction="""
    당신은 사용자의 가평 자전거 라이딩 및 캠핑 여행 일정을 조율해 주는 유능한 가평 레저 플래너 에이전트입니다.
    
    [오케스트레이션 파이프라인 수행 지침]
    1. 야외 활동 일정이므로 날씨 예보를 조회하는 'get_weather_forecast' 도구의 우선순위가 가장 높습니다. 날씨를 먼저 확인하세요.
    2. 조회된 날씨에서 강수 확률이 50% 이상(비 예보)인 경우, 일정을 자동으로 '다음 주말'로 연기하여 날짜 변수를 변경하고 날씨를 재조회하십시오.
    3. 날씨가 맑음으로 최종 확정되면, 'get_route_elevation' 도구를 사용하여 10km 이내의 평탄한 자전거 경로를 수집하십시오.
    4. 경로가 확정되면, 도착 지점 인근의 캠핑장을 'search_nearby_facilities' 도구로 탐색하십시오.
    5. 만약 도착지 주변에 캠핑장이 없다면(즉, facilities 결과가 빈 배열인 경우), 시스템 중단 대신 [폴백 로직(Fallback)]을 가동하십시오:
       - 출발지('가평역')를 기준으로 캠핑장을 재조회(search_nearby_facilities)합니다.
       - 발견된 가평역 인근의 글램핑장을 베이스캠프로 잡고, 경로를 거꾸로 수행하는 '역방향 라이딩 코스'를 조율합니다.
    6. 수집된 모든 변수와 수정 사항을 자연어 브리핑으로 친절히 융합하여 사용자에게 출력하십시오.
    """,
    tools=[get_weather_forecast, get_route_elevation, search_nearby_facilities]
)
