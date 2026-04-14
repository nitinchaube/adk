import json
import logging
import time
from typing import Any

logger = logging.getLogger("adk_monitor")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

def emit(event_type: str, **fields: Any) -> None:
    """Emit a structured JSON log line to stdout."""
    record = {
        "timestamp": time.time(),
        "event": event_type,
        **fields,
    }
    logger.info(json.dumps(record, default=str))


