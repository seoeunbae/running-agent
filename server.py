import re
import sys
import asyncio
import base64
import dotenv
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

dotenv.load_dotenv("/home/admin_seoeun_altostrat_com/running-agent/.env")
sys.path.append("/home/admin_seoeun_altostrat_com/running-agent")

from running_agent.agent import root_agent
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

app = FastAPI(title="Running Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Module-level singleton: preserves conversation history across requests
runner = InMemoryRunner(root_agent)
runner.auto_create_session = True

SESSION_USER_ID = "ui_user"
SESSION_ID = "ui_session"
MAX_TURNS = 7  # 유지할 최대 대화 턴 수


async def trim_session_history():
    """세션 히스토리를 MAX_TURNS 이내로 유지합니다."""
    try:
        session = await runner.session_service.get_session(
            app_name=root_agent.name,
            user_id=SESSION_USER_ID,
            session_id=SESSION_ID
        )
        if session and hasattr(session, 'events') and session.events:
            max_events = MAX_TURNS * 2
            if len(session.events) > max_events:
                session.events = session.events[-max_events:]
    except Exception:
        pass


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        events = []
        async for event in runner.run_async(
            user_id=SESSION_USER_ID,
            session_id=SESSION_ID,
            new_message=Content(role="user", parts=[Part.from_text(text=req.message)])
        ):
            events.append(event)

        await trim_session_history()

        serialized_events = []
        final_text = ""

        for event in events:
            author = getattr(event, "author", "Agent")

            # 1. Tool Calls
            if hasattr(event, "get_function_calls"):
                for call in event.get_function_calls():
                    serialized_events.append({
                        "type": "ToolCallEvent",
                        "tool_name": call.name,
                        "args": call.args if hasattr(call, "args") else {},
                        "agent_name": author
                    })

            # 2. Tool Responses
            if hasattr(event, "get_function_responses"):
                for resp in event.get_function_responses():
                    serialized_events.append({
                        "type": "ToolResponseEvent",
                        "tool_name": resp.name,
                        "response": resp.response if hasattr(resp, "response") else {},
                        "agent_name": author
                    })

            # 3. Text
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        serialized_events.append({
                            "type": "TextEvent",
                            "text": part.text,
                            "agent_name": author
                        })
                        final_text = part.text

        # Extract running course map image from ADK artifact service
        image_data = {}
        try:
            artifact_filename = None
            for event in events:
                if hasattr(event, "get_function_responses"):
                    for resp in event.get_function_responses():
                        if resp.name == "search_running_course":
                            match = re.search(r'artifact `([^`]+\.png)`', str(resp.response))
                            if match:
                                artifact_filename = match.group(1)
                                break

            if artifact_filename:
                artifact = await runner.artifact_service.load_artifact(
                    app_name=root_agent.name,
                    user_id=SESSION_USER_ID,
                    session_id=SESSION_ID,
                    filename=artifact_filename,
                )
                if artifact and artifact.inline_data and artifact.inline_data.data:
                    image_data = {
                        "filename": artifact_filename,
                        "data": base64.b64encode(artifact.inline_data.data).decode('utf-8'),
                        "mime_type": artifact.inline_data.mime_type or "image/png",
                    }
        except Exception as e:
            print(f"[image] artifact read error: {e}")

        return JSONResponse({
            "success": True,
            "text": final_text,
            "events": serialized_events,
            "image": image_data
        })
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/reset")
async def reset():
    """대화 세션을 초기화합니다."""
    try:
        session = await runner.session_service.get_session(
            app_name=root_agent.name,
            user_id=SESSION_USER_ID,
            session_id=SESSION_ID
        )
        if session:
            if hasattr(session, 'events'):
                session.events = []
            if hasattr(session, 'state'):
                session.state.clear()
        return JSONResponse({"success": True, "message": "대화가 초기화되었습니다."})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# Mount frontend
app.mount("/", StaticFiles(directory="/home/admin_seoeun_altostrat_com/running-agent/web", html=True), name="web")
