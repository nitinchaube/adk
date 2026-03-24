import os
import sys
from typing import Any

# Ensure ADK root is importable for "from Tools...." imports.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import BaseTool, ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from Tools.ExternalAPITool import search_books
from Tools.ShoppingCartTool import (
    add_to_cart,
    analyze_product_image,
    checkout,
    create_return_ticket,
    get_product_details,
)


async def save_shopping_memory(callback_context: CallbackContext):
    await callback_context.add_events_to_memory(
        events=callback_context.session.events[-5:-1]
    )
    return None


async def validate_before_tool(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
) -> dict | None:
    if tool.name == "checkout":
        cart = tool_context.state.get("user:cart", {"items": []})
        if not cart.get("items"):
            return {
                "error": "EMPTY_CART",
                "message": "Cannot checkout - cart is empty.",
            }

    if tool.name == "add_to_cart":
        valid_ids = ["PROD-001", "PROD-002", "PROD-003"]
        product_id = args.get("product_id")
        if product_id not in valid_ids:
            return {
                "error": "INVALID_PRODUCT",
                "message": f"Product '{product_id}' does not exist.",
            }

    return None


async def handle_tool_error(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
) -> dict | None:
    if isinstance(tool_response, dict) and "error" in tool_response:
        error_code = tool_response.get("error")
        print(f"[ERROR] Tool '{tool.name}' failed: {error_code}")
        tool_context.state["temp:error_count"] = (
            tool_context.state.get("temp:error_count", 0) + 1
        )
        if tool_context.state["temp:error_count"] >= 3:
            return {
                "error": "ESCALATE",
                "message": "Multiple failures detected. Escalating to human agent.",
            }

    return None


root_agent = LlmAgent(
    name="CustomerSupportLiveAgent",
    model="gemini-live-2.5-flash-native-audio",
    description="Live audio customer support agent for shopping cart, returns, and product queries.",
    instruction="""
    You are a multimodal shopping assistant with live voice support.
    You MUST use tools for product, cart, return, and books queries.

    SHOPPING:
    - Product questions -> get_product_details first.
    - Add only valid product ids.
    - Checkout only when user explicitly asks.

    IMAGE/VIDEO:
    - Analyze shown products with analyze_product_image.
    - Create return tickets for damaged/wrong products.

    KNOWLEDGE:
    - Use search_books for books/authors/recommendations questions.

    MEMORY:
    - Greet user by name if known.
    - Remember preferences and past details.
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
    generate_content_config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Aoede"
                )
            )
        ),
    ),
)
