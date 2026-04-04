"""Shared pytest configuration — loads ADK/.env before any test imports agents."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import dotenv

ADK_ROOT = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(ADK_ROOT / ".env")

sys.path.insert(0, str(ADK_ROOT))
