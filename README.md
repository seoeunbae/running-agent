# Google ADK Agent Orchestration & Fallback Backend

This repository contains a clean, production-ready Python backend implementation of an LLM agent utilizing Google's new open-source **Agent Development Kit (ADK)**. 

The agent models a leisure planning scenario (riding & camping in Gapyeong) and showcases:
1. **Explicit Tool Description (Docstrings as Schemas)**: Priority-based orchestration guided by tool docstrings.
2. **State & Context Management**: Real-time updates to requested dates when weather is unfavorable.
3. **Graceful Fallback Logic**: Handling destination facility absence by querying starting point facilities instead and suggesting a reverse routing plan.

---

## 📂 Project Structure

* `agent.py` - Core Python script defining mock tools and the `root_agent` using `google.adk`.
* `venv/` - Local Python virtual environment.

---

## ⚙️ How to Run and Test

Make sure your virtual environment is active and the Google Gemini credentials are set up.

### 1. Active Virtual Environment
```bash
source venv/bin/activate
```

### 2. Configure Credentials
The Google ADK relies on Vertex AI / Gemini. Set your API credentials:
```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
# Or if using Google Cloud / Vertex AI Application Default Credentials:
# gcloud auth application-default login
```

### 3. Run via ADK CLI (Terminal Interface)
You can converse with the agent directly in your terminal:
```bash
adk run --prompt "가평에서 이번 주말에 진행할 10km 평탄 코스와 캠핑장 검색해 줘."
```

### 4. Start the ADK Web Server (API / Local Swagger)
To expose the agent via FastAPI and stream token-level actions:
```bash
adk api_server
```
- Interactive API Docs (Swagger): `http://localhost:8000/docs`
- Streams endpoint: `POST http://localhost:8000/run_sse`

### 5. Launch the ADK Web Dashboard (Playground UI)
If you wish to test using the official Google ADK Web playground:
```bash
adk web
```
This launches a browser-based dashboard at `http://localhost:8080` (or `http://localhost:4200`) connected to your local agent code.

---

## 🛠️ Code Specifications (`agent.py`)

The agent is fully configured with three tools:
* `get_weather_forecast(location: str, date: str)`: Priority 1. Returns rain probabililty.
* `get_route_elevation(location: str, distance: str, max_elevation_gain: str)`: Priority 2. Returns cycling route details.
* `search_nearby_facilities(location: str, type: str, radius_km: int)`: Priority 3. Searches for campsites. If empty, triggers fallback parameters pointing to the starting coordinates and suggests a reverse routing flow.
