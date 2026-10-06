from __future__ import annotations

from typing import Any

import httpx


class WebSearcher:
    """Retrieve current search results through the DuckDuckGo Instant Answer API."""

    async def search(self, query: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1},
            )
            response.raise_for_status()
            data = response.json()
        return {
            "query": query,
            "abstract": data.get("AbstractText", ""),
            "source": data.get("AbstractURL", ""),
            "related_topics": [
                topic.get("Text", "")
                for topic in data.get("RelatedTopics", [])
                if isinstance(topic, dict) and topic.get("Text")
            ],
        }
