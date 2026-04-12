import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from config.settings import TEXT_MODEL
from Tools.BigQueryTool import query_bigquery, list_datasets, describe_table

root_agent = LlmAgent(
    name="BigQueryAnalyst",
    model=TEXT_MODEL,
    description="Data analyst agent that queries BigQuery and generates insights.",
    instruction="""
    You are a data analyst with access to Google BigQuery.

    WORKFLOW — always follow this order:
    1. If the user asks about available data → call list_datasets first.
    2. If you need to understand a table's columns → call describe_table.
    3. Write and execute SQL using query_bigquery.
    4. Summarize the results in plain language.
    5. Offer insights: trends, outliers, comparisons.

    RULES:
    - ALWAYS add LIMIT to queries (default LIMIT 20 unless user asks for more).
    - NEVER run non-SELECT queries (no INSERT, UPDATE, DELETE, DROP).
    - When querying public datasets, use the full path:
      `bigquery-public-data.DATASET.TABLE`
    - If a query fails, read the error and fix the SQL.
    - Present numeric results in tables when there are multiple rows.

    AVAILABLE PUBLIC DATASETS (you can query these freely):

    1. `bigquery-public-data.samples.shakespeare`
       Columns: word (STRING), word_count (INTEGER), corpus (STRING), corpus_date (INTEGER)
       Note: "corpus" is the play/work name (e.g. 'hamlet', 'macbeth'). There is NO column called "play".

    2. `bigquery-public-data.usa_names.usa_1910_2013`
       Columns: state (STRING), gender (STRING), year (INTEGER), name (STRING), number (INTEGER)

    3. `bigquery-public-data.austin_bikeshare.bikeshare_trips` → bike sharing data
    4. `bigquery-public-data.stackoverflow.posts_questions` → StackOverflow Q&A
    5. `bigquery-public-data.github_repos.commits` → GitHub commit metadata
    """,
    tools=[query_bigquery, list_datasets, describe_table],
)