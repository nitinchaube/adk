import re
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

PII_PATTERNS = {
    "SSN":         r"\b\d{3}-\d{2}-\d{4}\b",
    "email":       r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone":       r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
}

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts)",
    r"you\s+are\s+now\s+\w+",
    r"</?system>",
    r"print\s+(the\s+)?(system\s+)?prompt",
    r"act\s+as\s+(if\s+)?you\s+have\s+no\s+(restrictions|limits)",
    r"jailbreak",
    r"DAN\s+mode",
]


def _contains_pii(text: str) -> tuple[bool, str]:
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return True, pii_type
    return False, ""


def _contains_injection(text: str) -> bool:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _redact_pii(text: str) -> str:
    for pii_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[{pii_type.upper()} REDACTED]", text, flags=re.IGNORECASE)
    return text


def _make_blocked_response(message: str) -> LlmResponse:
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text=message)],
        )
    )


def input_guardrail(callback_context: CallbackContext, llm_request: LlmRequest) -> LlmResponse | None:
    """Fires BEFORE the LLM sees the message. Blocks injections and PII."""
    last_user_message = ""
    if llm_request.contents:
        parts = llm_request.contents[-1].parts
        if parts:
            last_user_message = parts[0].text or ""

    if _contains_injection(last_user_message):
        return _make_blocked_response(
            "⚠️ Request rejected: potential prompt injection detected."
        )

    has_pii, pii_type = _contains_pii(last_user_message)
    if has_pii:
        return _make_blocked_response(
            f"⚠️ Request rejected: please remove {pii_type} from your message."
        )

    return None


def output_guardrail(callback_context: CallbackContext, llm_response: LlmResponse) -> LlmResponse:
    """Fires AFTER the LLM responds — redacts any leaked PII."""
    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if part.text:
                part.text = _redact_pii(part.text)
    return llm_response
