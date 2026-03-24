import httpx

async def search_books(query: str, max_results: int = 3) -> dict:
    """
    Search Open Library for books matching the user's query.

    Use when the user asks about books, authors, reading recommendations,
    or anything unrelated to the in-store product catalog (PROD-001 etc.).

    Args:
        query: Search terms, e.g. "machine learning" or author name.
        max_results: Max number of titles to return (default 3).

    Returns:
        dict with key "books": list of {title, authors, first_publish_year} or "error".
    """
    url = "https://openlibrary.org/search.json"
    params = {"q": query, "limit": max_results}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    
    docs = data.get("docs", [])[:max_results]
    books = []
    for d in docs:
        books.append({
            "title": d.get("title"),
            "authors": d.get("author_name", []),
            "first_publish_year": d.get("first_publish_year"),
        })
    
    return {"books": books, "source": "openlibrary.org"}
