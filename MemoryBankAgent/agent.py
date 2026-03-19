from google import adk
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

async def generate_memory_callback(callback_context: CallbackContext):
    await callback_context.add_events_to_memory(
        events = callback_context.session.events[-5:-1] #adding last 5 events context into memory bank
    )
    return None

root_agent = adk.Agent(
    model = "gemini-2.5-flash",
    name = "memory_agent",
    instruction = "you are a helpful personal assistant. You remember facts about the user across conversation. Always greet the user by name if you know it.",
    tools = [PreloadMemoryTool()],
    after_agent_callback = generate_memory_callback
)
