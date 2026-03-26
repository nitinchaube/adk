"""Runtime settings: defaults with optional environment overrides (no secrets here)."""

from __future__ import annotations

import os

# --- Gemini / agents ---
TEXT_MODEL = os.environ.get("ADK_TEXT_MODEL", "gemini-2.5-flash")
LIVE_MODEL = os.environ.get("ADK_LIVE_MODEL", "gemini-live-2.5-flash-native-audio")
MEMORY_AGENT_MODEL = os.environ.get("ADK_MEMORY_AGENT_MODEL", "gemini-2.5-flash")

TEXT_AGENT_NAME = os.environ.get("ADK_TEXT_AGENT_NAME", "CustomerSupportTextAgent")
LIVE_AGENT_NAME = os.environ.get("ADK_LIVE_AGENT_NAME", "CustomerSupportLiveAgent")
MEMORY_AGENT_NAME = os.environ.get("ADK_MEMORY_AGENT_NAME", "memory_agent")

VOICE_NAME = os.environ.get("ADK_VOICE_NAME", "Aoede")

# --- Memory callbacks: events sent to Memory Bank (same semantics as events[-5:-1]) ---
MEMORY_EVENTS_SLICE_START = int(os.environ.get("ADK_MEMORY_EVENTS_SLICE_START", "-5"))
MEMORY_EVENTS_SLICE_END = int(os.environ.get("ADK_MEMORY_EVENTS_SLICE_END", "-1"))

# --- Tool guards ---
MAX_TOOL_ERRORS_BEFORE_ESCALATE = int(os.environ.get("ADK_MAX_TOOL_ERRORS_BEFORE_ESCALATE", "3"))

# --- Shopping / loyalty (session key kept for backward compatibility) ---
DEFAULT_LOYALTY_THRESHOLD = float(os.environ.get("ADK_DEFAULT_LOYALTY_THRESHOLD", "500"))
# Preferred (correct spelling) session key.
LOYALTY_STATE_KEY = "app:loyalty_threshold"
# Legacy key kept for backward compatibility with older sessions/instructions.
LOYALTY_STATE_KEY_LEGACY = "app:loyality_threshold"
LOYALTY_STATE_KEYS = (LOYALTY_STATE_KEY, LOYALTY_STATE_KEY_LEGACY)

ORDER_ID_PREFIX = os.environ.get("ADK_ORDER_ID_PREFIX", "ORD-")
TICKET_ID_PREFIX = os.environ.get("ADK_TICKET_ID_PREFIX", "TKT-")
RETURN_ESTIMATED_RESOLUTION = os.environ.get(
    "ADK_RETURN_ESTIMATED_RESOLUTION", "2-3 business days"
)

# --- Open Library ---
OPEN_LIBRARY_URL = os.environ.get(
    "ADK_OPEN_LIBRARY_URL", "https://openlibrary.org/search.json"
)
OPEN_LIBRARY_TIMEOUT_SEC = float(os.environ.get("ADK_OPEN_LIBRARY_TIMEOUT_SEC", "15"))
OPEN_LIBRARY_DEFAULT_LIMIT = int(os.environ.get("ADK_OPEN_LIBRARY_DEFAULT_LIMIT", "3"))
OPEN_LIBRARY_MAX_LIMIT = int(os.environ.get("ADK_OPEN_LIBRARY_MAX_LIMIT", "10"))
