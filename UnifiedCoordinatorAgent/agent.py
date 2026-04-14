import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
from config.settings import TEXT_MODEL
from config.monitoring import (
    composed_before_model,
    composed_after_model,
    monitor_after_agent,
)

from StatefulShoppingCartAgent.agent import root_agent as shopping_agent
from BigQueryAgent.agent import root_agent as bigquery_agent
from ResearchPipelineAgent.agent import root_agent as research_agent

from GithubAnalyzerAgent.agent import root_agent as github_agent

root_agent = LlmAgent(
    name = "UnifiedCoordinator",
    model = TEXT_MODEL,
    description = "Routes use requests to the appropriate specialist agent.",
    instruction="""
    You are a smart dispatcher. Analyze every user message and route it
    to the correct specialist:
    ROUTING RULES:
    - Shopping (add to cart, checkout, returns, product info, images)
        → call CustomerSupportTextAgent
    - Data queries (statistics, trends, SQL, BigQuery, Shakespeare, names)
        → call BigQueryAnalyst
    - GitHub (repo analysis, issues, contributors, open source)
        → call GitHubAnalyzerAgent
    - Research (explain a topic, fact-check, deep dive on a concept)
        → call CoordinatorAgent (the research pipeline)
    - General questions that don't fit above
        → answer directly yourself
    RULES:
    - ALWAYS dispatch to a specialist when possible. Don't answer yourself
        if a specialist can do better.
    - After receiving the specialist's response, present it cleanly to
        the user. Add a brief note about which specialist handled it.
    - If the request is ambiguous, ask the user to clarify.
    - You can call MULTIPLE specialists if the request spans categories.
    """,
    tools = [
        AgentTool(agent = shopping_agent),
        AgentTool(agent = bigquery_agent),
        AgentTool(agent = github_agent),
        AgentTool(agent = research_agent),
    ],
    before_model_callback=composed_before_model,
    after_model_callback=composed_after_model,
    after_agent_callback=monitor_after_agent,
)