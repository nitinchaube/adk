import os
import sys
from typing import Any

# Ensure ADK root is importable for "from Tools...." imports.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import BaseTool, ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from config.catalog import valid_product_ids
from config.guardrails import input_guardrail, output_guardrail
from config.settings import (
    MAX_TOOL_ERRORS_BEFORE_ESCALATE,
    MEMORY_EVENTS_SLICE_END,
    MEMORY_EVENTS_SLICE_START,
    TEXT_AGENT_NAME,
    TEXT_MODEL,
)

from Tools.ExternalAPITool import search_books
from Tools.ShoppingCartTool import (
    add_to_cart,
    analyze_product_image,
    checkout,
    create_return_ticket,
    get_product_details,
)


async def save_shopping_memory(callback_context: CallbackContext) -> None:
    try:
        sl = slice(MEMORY_EVENTS_SLICE_START, MEMORY_EVENTS_SLICE_END)
        await callback_context.add_events_to_memory(
            events=callback_context.session.events[sl],
        )
    except ValueError:
        pass


async def validate_before_tool(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
) -> dict[str, Any] | None:
    """
    Runs before every tool call.
    Return a dict to short-circuit tool execution; return None to continue.
    """
    if tool.name == "checkout":
        cart = tool_context.state.get("user:cart", {"items": []})
        if not cart.get("items"):
            return {
                "error": "EMPTY_CART",
                "message": "Cannot checkout — cart is empty.",
            }

    if tool.name == "add_to_cart":
        product_id = args.get("product_id")
        if product_id not in valid_product_ids():
            return {
                "error": "INVALID_PRODUCT",
                "message": f"Product '{product_id}' does not exist.",
            }

    return None


async def handle_tool_error(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Runs after every tool call.
    Return a dict to override tool response; return None to keep original response.
    """
    if isinstance(tool_response, dict) and "error" in tool_response:
        error_code = tool_response.get("error")
        print(f"[ERROR] Tool '{tool.name}' failed: {error_code}")

        tool_context.state["temp:error_count"] = (
            tool_context.state.get("temp:error_count", 0) + 1
        )

        if tool_context.state["temp:error_count"] >= MAX_TOOL_ERRORS_BEFORE_ESCALATE:
            return {
                "error": "ESCALATE",
                "message": "Multiple failures detected. Escalating to human agent.",
            }

    return None


root_agent = LlmAgent(
    name=TEXT_AGENT_NAME,
    model=TEXT_MODEL,
    description="Text-first customer support agent for shopping cart, returns, and product queries.",
    instruction="""
    You are a multimodal shopping assistant. You have tools for EVERY customer need.
    You MUST use your tools — NEVER say you cannot process something.

    IMAGE inputs — you MUST follow this sequence:
    1. ALWAYS call analyze_product_image first for ANY uploaded image.
    Describe what you see as the product_description argument.
    2. If the image shows a damaged/broken/wrong item → ALWAYS call create_return_ticket immediately.
    Use order_id='UNKNOWN' if the user hasn't provided one, then ask for it afterward.
    3. If the image shows a product for purchase → use the result to offer add_to_cart.

    NEVER respond with "I cannot process refunds" or "contact customer service".
    You ARE the customer service. Use your tools.

    MEMORY:
    - Always greet the user by name if known.
    - Remember preferences and past orders across sessions.
    """,
    tools=[
        add_to_cart,
        checkout,
        get_product_details,
        create_return_ticket,
        analyze_product_image,
        search_books,
        PreloadMemoryTool(),
    ],
    after_agent_callback=save_shopping_memory,
    before_tool_callback=validate_before_tool,
    after_tool_callback=handle_tool_error,
    before_model_callback=input_guardrail,
    after_model_callback=output_guardrail,
)


