import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
from config.monitoring import (
    composed_before_model,
    composed_after_model,
    monitor_after_agent,
)


research_agent = LlmAgent(
    name="ResearchAgent",
    model="gemini-2.5-flash",
    description="Find detailed researched, factual information about any topic.",
    instruction="""
        You are a research specialist. Given a topic or question:
  1. Provide comprehensive factual information.
  2. Include key concepts, history, and current state.
  3. Structure your response clearly with bullet points.
  4. Always note if something is uncertain or contested.
  Be thorough — your output feeds into a summarizer and fact-checker.
    """,
)

summary_agent = LlmAgent(
    name="SummaryAgent",
    model="gemini-2.5-flash",
    description="Condenses detailed research into a clear, readable summary.",
    instruction="""
    You are a professional summarizer. Given raw research:
  1. Distill the key points into 3-5 clear sentences.
  2. Use plain language — no jargon unless necessary.
  3. Keep the summary under 150 words.
  4. Preserve the most important facts, not the most interesting ones.
    """,
)

fact_check_agent = LlmAgent(
    name="FactCheckAgent",
    model="gemini-2.5-flash",
    description="Validates factual accuracy of research and flags uncertain claims.",
    instruction="""
  You are a fact-checker. Given a research text:
  1. Identify 3-5 specific factual claims made in the text.
  2. For each claim, assess: CONFIRMED / UNCERTAIN / LIKELY_FALSE.
  3. Flag anything that might be outdated, simplified, or misleading.
  4. Output a structured list: Claim → Verdict → Reason.
  """,
)

root_agent = LlmAgent(
    name="CoordinatorAgent",
    model="gemini-2.5-flash",
    description="Orchestrates research, summarization, and fact-checking for complex queries.",
    instruction="""
  You are a research coordinator. For any user question:
  STEP 1: Call ResearchAgent with the user's question.
          Store the result mentally as "raw research".
  STEP 2: Call SummaryAgent with the raw research from step 1.
          Store the result as "summary".
  STEP 3: Call FactCheckAgent with the raw research from step 1.
          Store the result as "fact check results".
  STEP 4: Compose a final response:
          - Start with the summary (from step 2).
          - Add a "Fact Check" section with verdicts (from step 3).
          - If any claims were UNCERTAIN or LIKELY_FALSE, mention it prominently.
  ALWAYS run all three steps before responding to the user.
  NEVER skip the fact-check step.
  """,
    tools=[
        AgentTool(agent=research_agent),
        AgentTool(agent=summary_agent),
        AgentTool(agent=fact_check_agent),
    ],
    before_model_callback=composed_before_model,
    after_model_callback=composed_after_model,
    after_agent_callback=monitor_after_agent,
)
