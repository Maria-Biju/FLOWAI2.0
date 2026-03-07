# mcp/tools/google_search.py

import os
import requests


def google_search_handler(args: dict):

    query = args.get("query", "").strip()
    if not query:
        return {"status": "error", "message": "Search query required"}

    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return {"status": "error", "message": "SERPAPI_KEY not configured"}

    try:
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google",
                "q": query,
                "api_key": api_key,
                "num": 5
            },
            timeout=20
        )

        data = response.json()

        snippets = []

        for item in data.get("organic_results", [])[:5]:
            snippet = item.get("snippet")
            if snippet:
                snippets.append(snippet)

        combined_text = " ".join(snippets)

        return {
            "status": "success",
            "text": combined_text[:2000]  # limit size
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


TOOL = {
    "name": "google_search",
    "description": "Search Google for real-time information",
    "schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string"
            }
        },
        "required": ["query"]
    },
    "handler": google_search_handler
}