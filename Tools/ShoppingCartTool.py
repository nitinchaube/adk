from __future__ import annotations

from datetime import datetime

from google.adk.tools import ToolContext
from pydantic import BaseModel, validator

from config.catalog import PRODUCTS, valid_product_ids
from config.settings import (
    DEFAULT_LOYALTY_THRESHOLD,
    LOYALTY_STATE_KEYS,
    ORDER_ID_PREFIX,
    RETURN_ESTIMATED_RESOLUTION,
    TICKET_ID_PREFIX,
)


class AddToCartInput(BaseModel):
    product_id: str
    quantity: int

    @validator("product_id")
    def product_must_exist(cls, v: str) -> str:
        if v not in PRODUCTS:
            raise ValueError(
                f"Invalid product_id '{v}'. Must be one of {list(valid_product_ids())}"
            )
        return v

    @validator("quantity")
    def quantity_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be at least 1")
        return v


async def add_to_cart(
    product_id: str, tool_context: ToolContext, quantity: int = 1
) -> dict:
    """Add validated catalog item to cart using price from config catalog."""

    try:
        validated = AddToCartInput(product_id=product_id, quantity=quantity)
    except ValueError as e:
        return {"error": str(e), "success": False}

    # Enforce stock availability at the tool level (LLM instructions are not a guarantee).
    if not PRODUCTS[validated.product_id]["in_stock"]:
        return {
            "error": "OUT_OF_STOCK",
            "message": f"Product '{validated.product_id}' is currently out of stock.",
            "success": False,
        }

    unit_price = PRODUCTS[validated.product_id]["price"]
    cart = tool_context.state.get("user:cart", {"items": [], "total": 0.0})
    cart["items"].append(
        {"id": validated.product_id, "qty": validated.quantity, "price": unit_price}
    )
    cart["total"] = sum(item["price"] * item["qty"] for item in cart["items"])

    tool_context.state["user:cart"] = cart
    tool_context.state["user:total_items"] = (
        tool_context.state.get("user:total_items", 0) + validated.quantity
    )
    tool_context.state["temp:last_action"] = f"Added {validated.product_id}"
    tool_context.state["temp:session_adds"] = (
        tool_context.state.get("temp:session_adds", 0) + 1
    )

    return {"success": True, "cart_total": cart["total"]}


async def checkout(tool_context: ToolContext) -> dict:
    """Finalize cart into an order; VIP threshold comes from config default + session override."""

    try:
        cart = tool_context.state.get("user:cart", {"items": [], "total": 0.0})

        if not cart["items"]:
            return {
                "error": "EMPTY_CART",
                "message": "Cart is empty. Add items before checking out.",
            }

        if cart["total"] <= 0:
            return {
                "error": "INVALID_TOTAL",
                "message": "Cart total is invalid. Please re-add items.",
            }

        tool_context.state["user:lifetime_value"] = (
            tool_context.state.get("user:lifetime_value", 0) + cart["total"]
        )
        tool_context.state["user:order_count"] = (
            tool_context.state.get("user:order_count", 0) + 1
        )

        threshold = DEFAULT_LOYALTY_THRESHOLD
        for k in LOYALTY_STATE_KEYS:
            v = tool_context.state.get(k)
            if v is not None:
                threshold = float(v)
                break
        if tool_context.state["user:lifetime_value"] > threshold:
            tool_context.state["user:is_vip"] = True

        tool_context.state["user:cart"] = {"items": [], "total": 0.0}

        return {
            "success": True,
            "order_id": f"{ORDER_ID_PREFIX}{datetime.now():%Y%m%d%H%M%S}",
        }

    except KeyError as e:
        return {
            "error": "STATE_CORRUPTED",
            "message": f"Session data is missing: {e}. Please start a new session.",
        }
    except Exception:
        return {
            "error": "UNEXPECTED",
            "message": "Something went wrong. Please try again.",
        }


async def get_product_details(product_id: str) -> dict:
    """Return catalog row for a product id."""

    if product_id in PRODUCTS:
        p = PRODUCTS[product_id]
        return {
            "status": "success",
            "name": p["name"],
            "price": p["price"],
            "in_stock": p["in_stock"],
        }
    return {
        "status": "error",
        "error_message": f"Product '{product_id}' not found.",
    }


async def analyze_product_image(
    product_description: str, tool_context: ToolContext
) -> dict:
    """Heuristic keyword match from catalog keywords."""

    desc_lower = product_description.lower()
    for product_id, info in PRODUCTS.items():
        if any(kw in desc_lower for kw in info["keywords"]):
            return {
                "identified_product": info["name"],
                "suggested_product_id": product_id,
                "confidence": "high",
            }

    return {
        "identified_product": "unknown",
        "suggested_product_id": None,
        "confidence": "low",
        "message": "Could not match to catalog. Ask user for the product ID.",
    }


async def create_return_ticket(
    reason: str,
    tool_context: ToolContext,
    order_id: str = "UNKNOWN",
    damage_description: str = "",
) -> dict:
    """Open a support ticket; id prefix and SLA text from config."""

    ticket_id = f"{TICKET_ID_PREFIX}{datetime.now():%Y%m%d%H%M%S}"
    tool_context.state["user:open_tickets"] = (
        tool_context.state.get("user:open_tickets", []) + [ticket_id]
    )
    return {
        "ticket_id": ticket_id,
        "status": "created",
        "reason": reason,
        "order_id": order_id,
        "damage_description": damage_description,
        "estimated_resolution": RETURN_ESTIMATED_RESOLUTION,
    }
