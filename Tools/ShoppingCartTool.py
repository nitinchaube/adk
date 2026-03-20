from google.adk.tools import ToolContext
from datetime import datetime
from google import adk

async def add_to_cart(product_id: str, tool_context: ToolContext, quantity: int = 1) -> dict:
    '''
    Adds a product to the shopping cart.

    Call this ONLY after confirming the product exists and is in stock.
    Do NOT call this if the user is just asking about a product — use
    get_product_details first.

    '''
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
    """
    Processes the cart and creates an order.

    Only call this when the user explicitly says they want to checkout,
    place an order, or complete their purchase. Never call this proactively.
    """

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


async def get_product_details(product_id: str)-> dict:
    """
    Retrieves the name, price, and stock availability for a given product.

    Use this tool when the user asks about a product before adding it to cart,
    or when you need to confirm the price of an item.

    Args:
        product_id: The unique product identifier, e.g. 'PROD-001'.

    Returns:
        A dict with keys: name, price, in_stock (bool), or an error message.
    """
    catalog = {
        "PROD-001": {"name": "Wireless Headphones", "price": 24.99, "in_stock": True},
        "PROD-002": {"name": "Phone Case",          "price": 9.99,  "in_stock": True},
        "PROD-003": {"name": "USB-C Cable",         "price": 14.99, "in_stock": False},
    }
    if product_id in catalog:
        return {"status": "success", **catalog[product_id]}
    return {"status": "error", "error_message": f"Product '{product_id}' not found."}


async def analyze_product_image(product_description: str, tool_context: ToolContext)->dict:
    """
    Analyzes an uploaded product image to identify the product.

    Use this tool when the user uploads or shares a photo of a product
    and wants to know what it is, or wants to add it to their cart.
    Do NOT use this for text-based product queries — use get_product_details instead.

    Args:
        image_data: Base64-encoded image string or a public image URL.
        tool_context: ADK context for session state access.

    Returns:
        dict with keys:
            - identified_product (str): Best matching product name.
            - suggested_product_id (str): Closest matching product ID from catalog.
            - confidence (str): 'high', 'medium', or 'low'.
            - description (str): Brief description of what was seen in the image.
    """
    catalog = {
        "PROD-001": {"name": "Wireless Headphones", "keywords": ["headphone", "headset", "earphone", "audio", "wireless"]},
        "PROD-002": {"name": "Phone",          "keywords": ["case", "cover", "phone", "mobile"]},
        "PROD-003": {"name": "USB-C Cable",         "keywords": ["cable", "usb", "charger", "cord"]},
    }
    desc_lower = product_description.lower()
    for product_id, info in catalog.items():
        if any(kw in desc_lower for kw in info["keywords"]):
            return {"identified_product": info["name"], "suggested_product_id": product_id, "confidence": "high"}
    return {"identified_product": "unknown", "suggested_product_id": None, "confidence": "low",
            "message": "Could not match to catalog. Ask user for the product ID."}

async def create_return_ticket(reason, tool_context, order_id= "UNKNOWN", damage_description = "") -> dict:
    """
    Creates a return or support ticket for an order.

    Use this when a user reports a damaged item, wrong item received,
    or wants to return a product. If the user shared a photo of damage,
    include the damage description extracted from the image.

    Args:
        reason: Reason for return — 'damaged', 'wrong_item', 'not_as_described', 'other'.
        order_id: The order ID from a previous checkout, format 'ORD-YYYYMMDDHHMMSS'.
        tool_context: ADK context for session state access.
        damage_description: Optional description of damage seen in uploaded photo.

    Returns:
        dict with keys:
            - ticket_id (str): Generated support ticket ID.
            - status (str): 'created'.
            - estimated_resolution (str): Estimated resolution timeframe.
    """
    from datetime import datetime
    ticket_id = f"TKT-{datetime.now():%Y%m%d%H%M%S}"
    tool_context.state["user:open_tickets"] = (
        tool_context.state.get("user:open_tickets", []) + [ticket_id]
    )
    return {
        "ticket_id": ticket_id,
        "status": "created",
        "reason": reason,
        "damage_description": damage_description,
        "estimated_resolution": "2-3 business days"
    }


