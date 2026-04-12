"""Demo script: BigQuery agent querying, summarizing, and generating insights."""

import asyncio
import os
import sys

from dotenv import load_dotenv

ADK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ADK_ROOT, ".env"))
sys.path.insert(0, ADK_ROOT)

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from BigQueryAgent.agent import root_agent


async def run_demo():
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="bq_demo",
        session_service=session_service,
    )
    session = await session_service.create_session(
        app_name="bq_demo", user_id="demo_user",
    )

    queries = [
        "What are the top 10 most common words across all of Shakespeare's works?",
        "Now compare Hamlet vs Macbeth — which play uses more unique words?",
        "What insights can you draw about Shakespeare's writing style from this data?",
    ]

    for user_msg in queries:
        print(f"\n{'='*60}")
        print(f"USER: {user_msg}")
        print(f"{'='*60}")

        async for event in runner.run_async(
            user_id="demo_user",
            session_id=session.id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=user_msg)],
            ),
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"\nAGENT: {part.text}")


if __name__ == "__main__":
    asyncio.run(run_demo())