"""Integration tests for GithubAnalyzerAgent — verifies the parallel
fan-out / gather pattern: 3 agents run in parallel, a gather agent combines
their results into a structured report.

These tests call the real Gemini + GitHub APIs.
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

APP_NAME = "test_github"
USER_ID = "test_user"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def send_message(runner: Runner, session: Any, text: str) -> str:
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


async def get_state(svc: InMemorySessionService, session: Any) -> dict:
    s = await svc.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id,
    )
    return dict(s.state)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def env():
    from GithubAnalyzerAgent.agent import root_agent

    svc = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=svc)
    session = await svc.create_session(app_name=APP_NAME, user_id=USER_ID)
    return runner, session, svc


# ---------------------------------------------------------------------------
# Tests — Parallel Fan-Out
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parallel_agents_all_contribute_to_report(env):
    """All 3 parallel sub-agents should execute and their data should reach the
    gather agent (verified via the final report content)."""
    runner, session, _ = env

    reply = await send_message(
        runner, session, "Analyze the python/cpython repository",
    )

    reply_lower = reply.lower()
    has_repo_data = any(w in reply_lower for w in ["star", "fork", "cpython", "python"])
    has_issue_data = any(w in reply_lower for w in ["issue", "bug", "open"])
    has_contributor_data = any(w in reply_lower for w in ["contributor", "commit", "author"])
    assert has_repo_data, f"Report missing repo metadata. Got: {reply[:300]}"
    assert has_issue_data or has_contributor_data, (
        f"Report missing issue or contributor data. Got: {reply[:300]}"
    )


@pytest.mark.asyncio
async def test_report_mentions_correct_repo(env):
    """The final report should reference the specific repo that was requested."""
    runner, session, _ = env

    reply = await send_message(runner, session, "Analyze python/cpython")

    assert "cpython" in reply.lower() or "python" in reply.lower(), (
        f"Report should mention the requested repo. Got: {reply[:300]}"
    )


# ---------------------------------------------------------------------------
# Tests — Gather Agent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gather_produces_report(env):
    """The final response should mention key report sections."""
    runner, session, _ = env

    reply = await send_message(
        runner, session, "Analyze the google/adk-python repository",
    )

    reply_lower = reply.lower()
    has_overview = any(w in reply_lower for w in ["overview", "star", "fork", "language"])
    has_issues = any(w in reply_lower for w in ["issue", "health", "bug"])
    has_community = any(w in reply_lower for w in ["contributor", "community", "commit"])
    assert has_overview, "Report should mention repo overview info"
    assert has_issues or has_community, "Report should mention issues or contributors"


# ---------------------------------------------------------------------------
# Tests — Error Handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nonexistent_repo_does_not_crash(env):
    """A non-existent repo should produce an error/message, not an exception."""
    runner, session, _ = env

    reply = await send_message(
        runner, session, "Analyze nonexistent-org-xyz/nonexistent-repo-xyz",
    )

    reply_lower = reply.lower()
    assert any(w in reply_lower for w in ["error", "not found", "could not", "unable", "404"]), (
        f"Expected error indication but got: {reply[:200]}"
    )


# ---------------------------------------------------------------------------
# Tests — Session Isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_separate_sessions_have_independent_state():
    """Two sessions should not share state from parallel agents."""
    from GithubAnalyzerAgent.agent import root_agent

    svc = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=svc)

    session_a = await svc.create_session(app_name=APP_NAME, user_id=USER_ID)
    session_b = await svc.create_session(app_name=APP_NAME, user_id=USER_ID)

    await send_message(runner, session_a, "Analyze python/cpython")

    state_b = await get_state(svc, session_b)
    assert "repo_info" not in state_b, "Session B should not have Session A's state"
