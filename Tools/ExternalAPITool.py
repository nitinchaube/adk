from __future__ import annotations

import httpx
from typing import Any

from config.settings import (
    OPEN_LIBRARY_DEFAULT_LIMIT,
    OPEN_LIBRARY_MAX_LIMIT,
    OPEN_LIBRARY_TIMEOUT_SEC,
    OPEN_LIBRARY_URL,
)


async def search_books(
    query: str,
    max_results: int = OPEN_LIBRARY_DEFAULT_LIMIT,
) -> dict[str, Any]:
    """
    Search Open Library for books matching the user's query.

    Use when the user asks about books, authors, reading recommendations,
    or anything unrelated to the in-store product catalog.

    Args:
        query: Search terms, e.g. "machine learning" or author name.
        max_results: Max number of titles to return (capped by config).

    Returns:
        dict with "books" list or "error" on failure.
    """
    limit = max(1, min(max_results, OPEN_LIBRARY_MAX_LIMIT))
    params = {"q": query, "limit": limit}
    try:
        async with httpx.AsyncClient(timeout=OPEN_LIBRARY_TIMEOUT_SEC) as client:
            r = await client.get(OPEN_LIBRARY_URL, params=params)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        return {"error": "HTTP_ERROR", "message": str(e), "books": []}
    except Exception as e:
        return {"error": "REQUEST_FAILED", "message": str(e), "books": []}

    docs = data.get("docs", [])[:limit]
    books = []
    for d in docs:
        books.append(
            {
                "title": d.get("title"),
                "authors": d.get("author_name", []),
                "first_publish_year": d.get("first_publish_year"),
            }
        )

    return {"books": books, "source": "openlibrary.org"}
