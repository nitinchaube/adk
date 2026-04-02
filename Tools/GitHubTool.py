from __future__ import annotations

from typing import Any

import httpx


GITHUB_API_BASE = "https://api.github.com"
GITHUB_TIMEOUT = 15.0


async def _github_get(path: str) -> dict[str, Any]:
    """Helper: authenticated GET against the GitHub REST API."""
    import os
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=GITHUB_TIMEOUT) as client:
        r = await client.get(f"{GITHUB_API_BASE}{path}", headers=headers)
        r.raise_for_status()
        return r.json()


async def get_repo_info(owner: str, repo: str) -> dict[str, Any]:
    """
    Get high-level info for a GitHub repository (stars, forks, language, description).

    Use when the user asks about a specific GitHub repo's overview or metadata.

    Args:
        owner: GitHub org or username, e.g. 'python'.
        repo: Repository name, e.g. 'cpython'.
    """
    try:
        data = await _github_get(f"/repos/{owner}/{repo}")
        return {
            "name": data.get("full_name"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "language": data.get("language"),
            "open_issues": data.get("open_issues_count"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
        }
    except httpx.HTTPError as e:
        return {"error": "GITHUB_API_ERROR", "message": str(e)}


async def get_repo_issues(owner: str, repo: str, limit: int = 5) -> dict[str, Any]:
    """
    Get the most recent open issues for a GitHub repository.

    Use when the user asks about recent bugs, feature requests, or open issues.

    Args:
        owner: GitHub org or username.
        repo: Repository name.
        limit: Max issues to return (default 5, max 30).
    """
    limit = max(1, min(limit, 30))
    try:
        data = await _github_get(f"/repos/{owner}/{repo}/issues?state=open&per_page={limit}")
        issues = []
        for item in data[:limit]:
            if "pull_request" not in item:  # skip PRs (they appear in /issues too)
                issues.append({
                    "number": item["number"],
                    "title": item["title"],
                    "state": item["state"],
                    "created_at": item["created_at"],
                    "labels": [l["name"] for l in item.get("labels", [])],
                })
        return {"issues": issues, "total_returned": len(issues)}
    except httpx.HTTPError as e:
        return {"error": "GITHUB_API_ERROR", "message": str(e)}


async def get_repo_contributors(owner: str, repo: str, limit: int = 5) -> dict[str, Any]:
    """
    Get top contributors for a GitHub repository by commit count.

    Use when the user asks who maintains or contributes to a repo.

    Args:
        owner: GitHub org or username.
        repo: Repository name.
        limit: Max contributors to return (default 5).
    """
    limit = max(1, min(limit, 30))
    try:
        data = await _github_get(f"/repos/{owner}/{repo}/contributors?per_page={limit}")
        contributors = []
        for c in data[:limit]:
            contributors.append({
                "username": c["login"],
                "contributions": c["contributions"],
            })
        return {"contributors": contributors}
    except httpx.HTTPError as e:
        return {"error": "GITHUB_API_ERROR", "message": str(e)}