from __future__ import annotations
import os
from typing import Any
from google.cloud import bigquery

BQ_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
MAX_ROWS = int(os.environ.get("ADK_BQ_MAX_ROWS", "50"))
MAX_BYTES_BILLED =  int(os.environ.get("ADK_BQ_MAX_BYTES", str(1*1024**3)))

def get_client()-> bigquery.Client:
    return bigquery.Client(project = BQ_PROJECT)

async def query_bigquery(sql: str) -> dict[str, Any]:
    """
    Run a read-only SQL query against Google BigQuery and return the results.
    Use this tool when the user asks questions about data, statistics,
    trends, or anything that requires querying a database. You can query
    any public BigQuery dataset or project-owned datasets.
    Common public datasets you can query:
    - bigquery-public-data.samples.shakespeare (word counts in Shakespeare)
    - bigquery-public-data.austin_bikeshare.bikeshare_trips (bike trip data)
    - bigquery-public-data.usa_names.usa_1910_2013 (US baby name popularity)
    - bigquery-public-data.github_repos.commits (GitHub commit history)
    - bigquery-public-data.stackoverflow.posts_questions (StackOverflow questions)
    IMPORTANT: Only SELECT queries are allowed. Never run INSERT, UPDATE,
    DELETE, DROP, or CREATE statements.
    Args:
        sql: A read-only SQL query (SELECT only). Always include LIMIT
            to avoid scanning too much data.
    """
    sql_striped = sql.strip().rstrip(";")
    first_word = sql_striped.split()[0].upper() if sql_striped else ""
    if first_word!="SELECT":
        return {
            "error":"UNSAFE_QUERY",
            "message": "Only SELECT Query are allowed. No INSERT/UPDATE/DELETE/DROP/CREATE"
        }
    
    try:
        client = get_client()
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed = MAX_BYTES_BILLED,
        )
        query_job = client.query(sql_striped, job_config=job_config)
        result = query_job.result(max_results=MAX_ROWS)
        columns = [field.name for field in result.schema]
        rows = list(result)

        if not rows:
            return {"row_count": 0, "columns": columns, "rows": [], "message": "Query returned no results."}

        result_rows = [
            {col: _serialize(row[col]) for col in columns}
            for row in rows
        ]

        return {
            "row_count": len(result_rows),
            "total_rows": result.total_rows,
            "columns": columns,
            "rows": result_rows,
            "bytes_processed": query_job.total_bytes_processed,
            "bytes_billed": query_job.total_bytes_billed,
        }

    except Exception as e:
        return {"error": "QUERY_FAILED", "message": str(e)}
    
def _serialize(value: Any)-> Any:
    """Convert BigQuery types to JSON-safe types."""
    import datetime
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value

async def list_datasets() -> dict[str, Any]:
    """
    List all datasets available in the current Google Cloud project.
    Use this when the user asks what data is available or wants to explore
    the project's datasets before querying.
    """
    try:
        client = get_client()
        datasets = [ds.dataset_id for ds in client.list_datasets()]
        return {"project": BQ_PROJECT, "datasets": datasets}
    except Exception as e:
        return {"error": "LIST_FAILED", "message": str(e)}
    
async def describe_table(dataset: str, table: str) -> dict[str, Any]:
    """
    Get the schema (column names, types) of a BigQuery table.
    Use this when the user asks about the structure of a table, or before
    writing a query to understand what columns are available.
    Args:
        dataset: The dataset name, e.g. 'samples' or 'usa_names'.
                For public data, use the full path like
                'bigquery-public-data.samples'.
        table: The table name, e.g. 'shakespeare' or 'usa_1910_2013'.
    """
    try:
        client = get_client()
        if "." in dataset:
            table_ref = f"{dataset}.{table}"
        else:
            table_ref = f"{BQ_PROJECT}.{dataset}.{table}"
        table_obj = client.get_table(table_ref)
        schema = [
            {"name": f.name, "type": f.field_type, "mode": f.mode, "description": f.description or ""}
            for f in table_obj.schema
        ]
        return {
            "table": table_ref,
            "num_rows": table_obj.num_rows,
            "size_mb": round(table_obj.num_bytes / (1024 * 1024), 2),
            "schema": schema,
        }
    except Exception as e:
        return {"error": "DESCRIBE_FAILED", "message": str(e)}