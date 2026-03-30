"""
SearXNG search tool for CrewAI agents.
Queries the self-hosted SearXNG instance and returns structured results.
"""
import os
from typing import Optional, Type
from pydantic import BaseModel, Field

try:
    import httpx
    from crewai.tools import BaseTool
except ImportError:
    raise ImportError("crewai and httpx are required: pip install crewai httpx")

SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://searxng:8080")


class SearXNGInput(BaseModel):
    query: str = Field(..., description="The search query to look up.")
    num_results: Optional[int] = Field(5, description="Number of results to return (default 5, max 20).")


class SearXNGTool(BaseTool):
    name: str = "Web Search (SearXNG)"
    description: str = (
        "Search the web using the self-hosted SearXNG metasearch engine. "
        "Aggregates results from Google, Bing, DuckDuckGo and more. "
        "Use this for current events, research, fact-checking, or any web query."
    )
    args_schema: Type[BaseModel] = SearXNGInput

    def _run(self, query: str, num_results: int = 5) -> str:
        num_results = min(int(num_results), 20)
        try:
            response = httpx.get(
                f"{SEARXNG_URL}/search",
                params={"q": query, "format": "json", "pageno": 1},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            return f"Search failed: {exc}"
        except Exception as exc:
            return f"Unexpected error during search: {exc}"

        results = data.get("results", [])[:num_results]
        if not results:
            return f"No results found for: {query}"

        lines = [f"Search results for: {query}\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("url", "")
            snippet = r.get("content", "No description available.")
            lines.append(f"{i}. {title}\n   URL: {url}\n   {snippet}\n")

        return "\n".join(lines)
