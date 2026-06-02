from google.adk import Agent
from .prompts import RUNNING_INSTRUCTION
from .tools import get_tools

root_agent = Agent(
    name="RunningPlanner",
    model="gemini-2.5-flash",
    instruction=RUNNING_INSTRUCTION,
    tools=get_tools(),
)
