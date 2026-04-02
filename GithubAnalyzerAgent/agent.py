import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from Tools.GitHubTool import get_repo_info, get_repo_issues, get_repo_contributors


repo_info_agent = LlmAgent(
    name = "RepoInfoAgent",
    model="gemini-2.5-flash",
    description="Fetches repository metadata (stars, forks, language).",
    instruction="""
    Extract the GitHub owner and repo from the user query.
    Call get_repo_info with those values.
    Store the result in state['repo_info'].
    Respond with a brief summary of the repo metadata.
    """,
    tools=[get_repo_info],
)

issue_tracker_agent = LlmAgent(
  name="IssueTrackerAgent",
  model="gemini-2.5-flash",
  description="Fetches recent open issues for a repository.",
  instruction="""
  Extract the GitHub owner and repo from the user query.
  Call get_repo_issues to get the 5 most recent open issues.
  Store the result in state['recent_issues'].
  Respond with the issue titles and labels.
  """,
  tools=[get_repo_issues],
)

contributor_agent = LlmAgent(
  name="ContributorAgent",
  model="gemini-2.5-flash",
  description="Fetches top contributors for a repository.",
  instruction="""
  Extract the GitHub owner and repo from the user query.
  Call get_repo_contributors to get the top 5 contributors.
  Store the result in state['top_contributors'].
  Respond with the contributor usernames and their commit counts.
  """,
  tools=[get_repo_contributors],
)


# -- fan-out stage
parallel_stage = ParallelAgent(
    name = "GitHubDataGatherer",
    sub_agents = [repo_info_agent, issue_tracker_agent, contributor_agent]

)

# -- Gather stage

gather_agent = LlmAgent(
    name= "GatherAgent",
    model="gemini-2.5-flash",
    description="Aggregates parallel analysis results into a final report.",
    instruction="""
    You are a report writer. Read the following from session state:
    - state['repo_info']       → repository metadata
    - state['recent_issues']   → recent open issues
    - state['top_contributors']→ top contributors
    Compose a structured GitHub Repository Analysis Report with sections:
    1. Overview (name, description, stars, forks, language)
    2. Health (open issue count, recent issue themes)
    3. Community (top contributors and their activity)
    4. Summary verdict (is this repo active, healthy, well-maintained?)
    Be concise but informative.
    """,
)

root_agent = SequentialAgent(
    name = "GitHubAnalyzerAgent",
    sub_agents = [parallel_stage, gather_agent]
)