"""
Enterprise monitoring callbacks for ADK agents.

Each callback emits a structured JSON log line via config.logging.emit.
Usage — replace raw guardrail callbacks with the composed versions:

    before_model_callback = composed_before_model
    after_model_callback  = composed_after_model
    before_tool_callback  = monitor_before_tool
    after_tool_callback   = monitor_after_tool
    after_agent_callback  = monitor_after_agent
"""

import time
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools import BaseTool, ToolContext

from config.guardrails import input_guardrail, output_guardrail
from config.logging import emit


# ---------------------------------------------------------------------------
# Low-level model callbacks
# ---------------------------------------------------------------------------

def monitor_before_model(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> LlmResponse | None:
    """Record the start of an LLM call and store timestamp in temp state."""
    callback_context.state["temp:llm_start"] = time.time()
    num_messages = len(llm_request.contents) if llm_request.contents else 0
    emit(
        "llm_call_start",
        agent=callback_context.agent_name,
        model=str(getattr(llm_request, "model", "unknown")),
        num_messages=num_messages,
    )
    return None


def monitor_after_model(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse:
    """Record LLM latency and token usage after the model responds."""
    start = callback_context.state.get("temp:llm_start", time.time())
    duration_ms = round((time.time() - start) * 1000)

    usage = getattr(llm_response, "usage_metadata", None)
    # Gemini/Vertex AI attribute names
    input_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
    output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

    has_tool_call = False
    if llm_response.content and llm_response.content.parts:
        has_tool_call = any(
            getattr(p, "function_call", None) for p in llm_response.content.parts
        )

    emit(
        "llm_call_end",
        agent=callback_context.agent_name,
        duration_ms=duration_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        has_tool_call=has_tool_call,
    )

    # Accumulate counters in temp state for the agent-level summary
    callback_context.state["temp:total_input_tokens"] = (
        callback_context.state.get("temp:total_input_tokens", 0) + input_tokens
    )
    callback_context.state["temp:total_output_tokens"] = (
        callback_context.state.get("temp:total_output_tokens", 0) + output_tokens
    )
    callback_context.state["temp:llm_call_count"] = (
        callback_context.state.get("temp:llm_call_count", 0) + 1
    )
    return llm_response


# ---------------------------------------------------------------------------
# Low-level tool callbacks
# ---------------------------------------------------------------------------

async def monitor_before_tool(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
) -> dict[str, Any] | None:
    """Record when a tool call starts."""
    tool_context.state["temp:tool_start"] = time.time()
    emit(
        "tool_call_start",
        agent=tool_context.agent_name,
        tool=tool.name,
        args=args,
    )
    return None


async def monitor_after_tool(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict[str, Any],
) -> dict[str, Any] | None:
    """Record tool latency and success/failure."""
    start = tool_context.state.get("temp:tool_start", time.time())
    duration_ms = round((time.time() - start) * 1000)

    is_error = isinstance(tool_response, dict) and "error" in tool_response
    error_code = tool_response.get("error") if is_error else None

    emit(
        "tool_call_end",
        agent=tool_context.agent_name,
        tool=tool.name,
        duration_ms=duration_ms,
        success=not is_error,
        error_code=error_code,
    )

    # Accumulate counters for the agent-level summary
    tool_context.state["temp:tool_call_count"] = (
        tool_context.state.get("temp:tool_call_count", 0) + 1
    )
    if is_error:
        tool_context.state["temp:tool_error_count"] = (
            tool_context.state.get("temp:tool_error_count", 0) + 1
        )
    return None


# ---------------------------------------------------------------------------
# Agent lifecycle callback
# ---------------------------------------------------------------------------

async def monitor_after_agent(callback_context: CallbackContext) -> None:
    """Emit a single summary event when an agent turn completes."""
    emit(
        "agent_turn_complete",
        agent=callback_context.agent_name,
        session_id=callback_context.session.id,
        llm_calls=callback_context.state.get("temp:llm_call_count", 0),
        tool_calls=callback_context.state.get("temp:tool_call_count", 0),
        tool_errors=callback_context.state.get("temp:tool_error_count", 0),
        total_input_tokens=callback_context.state.get("temp:total_input_tokens", 0),
        total_output_tokens=callback_context.state.get("temp:total_output_tokens", 0),
    )


# ---------------------------------------------------------------------------
# Composed callbacks (monitoring + guardrails in one call)
# These replace the raw guardrail callbacks in every LlmAgent.
# ---------------------------------------------------------------------------

def composed_before_model(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> LlmResponse | None:
    """Run monitoring, then apply the input guardrail."""
    monitor_before_model(callback_context, llm_request)
    return input_guardrail(callback_context, llm_request)


def composed_after_model(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse:
    """Run monitoring, then apply the output guardrail (PII redaction)."""
    llm_response = monitor_after_model(callback_context, llm_response)
    return output_guardrail(callback_context, llm_response)
