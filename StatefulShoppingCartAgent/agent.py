from google.adk.agents import Agent
from google.adk.tools import ToolContext
from datetime import datetime
from Tools.ShoppingCartTool import get_product_details, checkout, add_to_cart, analyze_product_image, create_return_ticket
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
import sys, os
from google.genai import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def save_shopping_memory(callback_context: CallbackContext):
    await callback_context.add_events_to_memory(
        events = callback_context.session.events[-5:-1]
    )
    return None


root_agent = Agent(
    name = "CustomerSupportAgent",
    model= "gemini-live-2.5-flash-native-audio",
    instruction ="""
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
    tools = [
        add_to_cart, 
        checkout, 
        get_product_details, 
        create_return_ticket,
        analyze_product_image,
        PreloadMemoryTool()
    ],
    after_agent_callback = save_shopping_memory,
    generate_content_config = types.GenerateContentConfig(
        response_modalities = ["AUDIO"],
        speech_config = types.SpeechConfig(
            voice_config = types.VoiceConfig(
                prebuilt_voice_config = types.PrebuiltVoiceConfig(
                    voice_name = "Aoede"
                )
            )
        )
    )
)


