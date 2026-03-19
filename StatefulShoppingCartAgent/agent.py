from google.adk.agents import Agent
from google.adk.tools import ToolContext
from datetime import datetime
from Tools.ShoppingCartTool import get_product_details, checkout, add_to_cart



root_agent = Agent(
    name = "CustomerSupportAgent",
    model= "gemini-2.5-flash",
    instruction = " Shopping cart agent demonstrating  temp:, user:, and app: state scopes.",
    tools = [add_to_cart, checkout, get_product_details]
)


