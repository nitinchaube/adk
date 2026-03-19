from google.adk.agents import Agent
from google.adk.tools import ToolContext
from datetime import datetime
from Tools.ShoppingCartTool import get_product_details, checkout, add_to_cart
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool


async def save_shopping_memory(callback_context: CallbackContext):
    await callback_context.add_events_to_memory(
        events = callback_context.session.events[-5:-1]
    )
    return None


root_agent = Agent(
    name = "CustomerSupportAgent",
    model= "gemini-2.5-flash",
    instruction = """ You are a helpful shopping assistant. 
        Always remember the user's name and personal details they share.
        At the start of every conversation, use the memory tool to recall past information about this user.
        Greet the user by name if you know it.
        Help with adding items to cart, checkout, and product queries
    """,
    tools = [add_to_cart, checkout, get_product_details, PreloadMemoryTool()],
    after_agent_callback = save_shopping_memory
)


