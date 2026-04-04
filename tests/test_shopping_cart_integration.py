"""Integration tests for StatefulShoppingCartAgent — verifies session state
persistence, callback guards, and end-to-end purchase flows.

These tests call the real Gemini API via ADK's Runner so they require a valid
GOOGLE_API_KEY (or Vertex AI credentials).
"""

from __future__ import annotations

import os
import sys
from typing import Any

import pytest
import pytest_asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

APP_NAME = "test_shopping"
USER_ID = "test_user"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def send_message(runner: Runner, session: Any, text: str) -> str:
    """Send a user message and return concatenated agent text."""
    parts: list[str] = []
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=text)],
        ),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    parts.append(part.text)
    return " ".join(parts)


async def get_state(
    svc: InMemorySessionService, session: Any, user_id: str = USER_ID,
) -> dict:
    """Fetch latest session state."""
    s = await svc.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session.id,
    )
    return dict(s.state)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def env():
    from StatefulShoppingCartAgent.agent import root_agent

    svc = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=svc)
    session = await svc.create_session(app_name=APP_NAME, user_id=USER_ID)
    return runner, session, svc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_valid_product_updates_cart(env):
    """Adding PROD-001 should create user:cart with at least one item."""
    runner, session, svc = env

    await send_message(runner, session, "Add PROD-001 to my cart")

    state = await get_state(svc, session)
    cart = state.get("user:cart", {})
    assert len(cart.get("items", [])) >= 1
    assert cart["total"] > 0


@pytest.mark.asyncio
async def test_add_invalid_product_rejected(env):
    """before_tool_callback should block PROD-999."""
    runner, session, svc = env

    reply = await send_message(runner, session, "Add PROD-999 to my cart")

    assert "not" in reply.lower() or "invalid" in reply.lower() or "exist" in reply.lower()
    state = await get_state(svc, session)
    cart = state.get("user:cart", {"items": []})
    assert len(cart.get("items", [])) == 0


@pytest.mark.asyncio
async def test_checkout_empty_cart_blocked(env):
    """before_tool_callback should prevent checkout when cart is empty."""
    runner, session, _ = env

    reply = await send_message(runner, session, "Checkout my order now please")

    assert "empty" in reply.lower() or "add" in reply.lower() or "cannot" in reply.lower()


@pytest.mark.asyncio
async def test_state_persists_across_turns(env):
    """Items added in turn 1 should still be visible in turn 2."""
    runner, session, svc = env

    await send_message(runner, session, "Add PROD-001 to cart")
    await send_message(runner, session, "Also add PROD-002 to cart")

    state = await get_state(svc, session)
    cart = state.get("user:cart", {})
    items = cart.get("items", [])
    assert len(items) >= 2, f"Expected >=2 items but got {len(items)}"


@pytest.mark.asyncio
async def test_full_purchase_flow(env):
    """Add → Checkout → verify order_count incremented."""
    runner, session, svc = env

    await send_message(runner, session, "Add PROD-001 to my cart, quantity 1")
    await send_message(runner, session, "Checkout")

    state = await get_state(svc, session)
    assert state.get("user:order_count", 0) >= 1
    assert state.get("user:lifetime_value", 0) > 0
    cart = state.get("user:cart", {})
    assert len(cart.get("items", [])) == 0, "Cart should be empty after checkout"


@pytest.mark.asyncio
async def test_return_ticket_stored_in_state(env):
    """create_return_ticket should write ticket ID into user:open_tickets."""
    runner, session, svc = env

    await send_message(
        runner, session,
        "I need to return order ORD-123 because the headphones arrived damaged",
    )

    state = await get_state(svc, session)
    tickets = state.get("user:open_tickets", [])
    assert len(tickets) >= 1
    assert tickets[0].startswith("TKT-")


@pytest.mark.asyncio
async def test_out_of_stock_product_rejected(env):
    """PROD-003 is out of stock — tool should reject."""
    runner, session, svc = env

    reply = await send_message(runner, session, "Add PROD-003 to my cart")

    reply_lower = reply.lower()
    assert "out of stock" in reply_lower or "unavailable" in reply_lower or "stock" in reply_lower

    state = await get_state(svc, session)
    cart = state.get("user:cart", {"items": []})
    assert len(cart.get("items", [])) == 0


@pytest.mark.asyncio
async def test_session_isolation_different_users():
    """Different users should have completely independent state."""
    from StatefulShoppingCartAgent.agent import root_agent

    svc = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=svc)

    session_a = await svc.create_session(app_name=APP_NAME, user_id="user_alice")
    session_b = await svc.create_session(app_name=APP_NAME, user_id="user_bob")

    await send_message(runner, session_a, "Add PROD-001 to my cart")

    state_a = (await svc.get_session(
        app_name=APP_NAME, user_id="user_alice", session_id=session_a.id,
    )).state
    state_b = (await svc.get_session(
        app_name=APP_NAME, user_id="user_bob", session_id=session_b.id,
    )).state

    assert len(state_a.get("user:cart", {}).get("items", [])) >= 1
    assert len(state_b.get("user:cart", {}).get("items", [])) == 0, (
        "Bob's cart should be unaffected by Alice's actions"
    )


@pytest.mark.asyncio
async def test_user_state_shared_across_sessions():
    """user: state for the SAME user_id is shared across sessions (ADK design)."""
    from StatefulShoppingCartAgent.agent import root_agent

    svc = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=svc)

    session_1 = await svc.create_session(app_name=APP_NAME, user_id="user_shared")
    session_2 = await svc.create_session(app_name=APP_NAME, user_id="user_shared")

    await send_message(runner, session_1, "Add PROD-001 to my cart")

    state_2 = (await svc.get_session(
        app_name=APP_NAME, user_id="user_shared", session_id=session_2.id,
    )).state

    assert len(state_2.get("user:cart", {}).get("items", [])) >= 1, (
        "user: state should be visible across sessions for the same user_id"
    )
