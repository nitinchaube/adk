from google.adk.agents import Agent
from google.adk.tools import ToolContext
from datetime import datetime

async def add_to_cart(product_id: str, tool_context: ToolContext, quantity: int = 1) -> dict:
    # user state
    cart = tool_context.state.get("user:cart", {"items": [], "total": 0.0})
    # add the item
    cart["items"].append({"id": product_id, "qty": quantity, "price": 24.99})
    cart["total"] = sum(item["price"]*item["qty"] for item in cart["items"])

    # updating user state
    tool_context.state["user:cart"] = cart
    tool_context.state["user:total_items"] = (
        tool_context.state.get("user:total_items", 0) + quantity
    )

    # temp_state: 
    tool_context.state["temp:last_action"] = f"Added {product_id}"
    tool_context.state["temp:session_adds"] = (
        tool_context.state.get("temp:session_adds", 0)+1
    )

    return {"success": True, "cart_total": cart["total"]}

async def checkout(tool_context: ToolContext) -> dict:
    cart = tool_context.state.get("user:cart", {"items":[], "total": 0.0})
    if not cart["items"]:
        return {"error": "Empty Cart"}
    
    # Update the user state
    tool_context.state["user:lifetime_value"] = (
        tool_context.state.get("user:lifetime_value", 0) + cart["total"]
    )
    tool_context.state["user:order_count"] = (
        tool_context.state.get("user:order_count", 0) + 1
    )

    if (tool_context.state["user:lifetime_value"] > tool_context.state.get("app:loyality_threshold", 500)):
        tool_context.state["user:is_vip"] = True

    #clear cart
    tool_context.state["user:cart"] = {"items": [], "total": 0.0}

    return {"success": True, "order_id": f"ORD-{datetime.now():%Y%m%d%H%M%S}"}


root_agent = Agent(
    name = "CustomerSupportAgent",
    model= "gemini-2.5-flash",
    instruction = " Shopping cart agent demonstrating  temp:, user:, and app: state scopes.",
    tools = [add_to_cart,checkout]
)


