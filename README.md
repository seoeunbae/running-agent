# Running Planner Agent

Google ADK 기반의 러닝 코스 플래닝 에이전트입니다. 사용자의 위치·날짜·거리 입력을 받아 날씨 확인 → 코스 추천 → 편의시설 탐색 → Google Maps 시각화까지 4단계 워크플로를 자동 실행합니다.

---

## 📂 Project Structure

```
running-agent/
├── running_agent/          # 에이전트 패키지
│   ├── __init__.py
│   ├── agent.py            # root_agent 정의 (gemini-2.5-flash)
│   ├── prompts.py          # PromptBuilder로 조립한 시스템 인스트럭션
│   ├── tools.py            # 4개 툴 구현체 + 내부 헬퍼
│   ├── utils.py            # PromptBuilder 유틸리티 클래스
│   └── skills/             # 스킬별 문서
│       ├── weather/
│       ├── route-planner/
│       ├── facility-finder/
│       └── map-visualizer/
├── web/                    # 커스텀 프론트엔드 (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── server.py               # FastAPI 서버 (/api/chat, /api/reset)
├── requirements.txt
└── .env                    # API 키 설정
```

---

## 🛠️ Tools (4-Step Pipeline)

| 순서 | 스킬 | 함수 | 역할 |
|------|------|------|------|
| 1 | `weather` | `get_weather_forecast` | 날씨·강수 확률 확인. 강수 ≥ 50% 시 일정 재조정 |
| 2 | `route-planner` | `get_route_elevation` | 거리·고도 기반 러닝 코스 선정 |
| 3 | `facility-finder` | `search_nearby_facilities` | 출발지 반경 편의점·카페·화장실 탐색 |
| 4 | `map-visualizer` | `search_running_course` | Google Maps 실데이터 기반 코스 탐색 + 지도 이미지 생성 (Artifact) |

---

## ⚙️ How to Run

### 1. 가상환경 활성화

```bash
source venv/bin/activate
```

### 2. 환경 변수 설정

`.env` 파일에 아래 키를 설정합니다.

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY   # 지도 이미지 생성에 필요
```

### 3. Custom UI 서버 실행 (권장)

FastAPI 서버와 프론트엔드를 함께 구동합니다.

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

- 웹 UI: `http://localhost:8000`
- API Docs (Swagger): `http://localhost:8000/docs`

#### API Endpoints

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/api/chat` | 메시지 전송, 툴 이벤트·텍스트·이미지 반환 |
| `POST` | `/api/reset` | 대화 세션 초기화 |

### 4. ADK CLI로 실행

```bash
adk run --prompt "마포구에서 다음 주말에 5km 러닝 코스 추천해줘."
```

### 5. ADK Web Playground

```bash
adk web
```

`http://localhost:8080` 에서 ADK 내장 플레이그라운드를 사용할 수 있습니다.

---

## 🏗️ Architecture

### Agent (`running_agent/agent.py`)

`google.adk.Agent`로 정의된 `RunningPlanner`. 모델은 `gemini-2.5-flash`, `get_tools()`에서 4개 툴을 주입받습니다.

### Prompts (`running_agent/prompts.py`)

`PromptBuilder`를 사용해 `role` → `rules` → `skills` → `tools` → `workflow` 섹션을 순서대로 조립합니다. 각 섹션은 독립 상수로 관리되어 재사용·오버라이드가 용이합니다.

### Server (`server.py`)

`InMemoryRunner` 싱글턴으로 세션을 유지합니다. `/api/chat` 응답에는 툴 호출 이벤트(`ToolCallEvent`), 툴 응답(`ToolResponseEvent`), 텍스트(`TextEvent`), 지도 이미지(Base64)가 포함됩니다.
