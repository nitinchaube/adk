import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import adk
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from config.settings import (
    MEMORY_AGENT_MODEL,
    MEMORY_AGENT_NAME,
    MEMORY_EVENTS_SLICE_END,
    MEMORY_EVENTS_SLICE_START,
)


async def generate_memory_callback(callback_context: CallbackContext) -> None:
    try:
        sl = slice(MEMORY_EVENTS_SLICE_START, MEMORY_EVENTS_SLICE_END)
        await callback_context.add_events_to_memory(
            events=callback_context.session.events[sl],
        )
    except ValueError:
        pass


root_agent = adk.Agent(
    model=MEMORY_AGENT_MODEL,
    name=MEMORY_AGENT_NAME,
    instruction=(
        "You are a helpful personal assistant. You remember facts about the user "
        "across conversations. Always greet the user by name if you know it."
    ),
    tools=[PreloadMemoryTool()],
    after_agent_callback=generate_memory_callback,
)
