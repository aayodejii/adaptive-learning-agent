"""
Tool 3: Real-Time Resource Search
Finds external learning resources using web search APIs
"""

import os
import requests
from datetime import datetime
from typing import Optional, Type, List

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from models.schemas import ResourceLink, ResourceSearchResult


class ResourceSearchInput(BaseModel):
    """Input schema for Resource Search"""

    query: str = Field(..., description="Search query for learning resources")
    max_results: int = Field(
        default=5, ge=1, le=10, description="Maximum number of results to return"
    )


class RealTimeResourceSearch(BaseTool):
    """
    Custom LangChain tool for searching external learning resources.

    Integrates with Tavily API (or Google Custom Search) to find
    relevant educational content, tutorials, and documentation.
    """

    name: str = "real_time_resource_search"
    description: str = """
    Searches the web for educational resources, tutorials, and documentation.
    
    Use this tool when:
    - User asks for learning materials, tutorials, or resources
    - User wants external references to supplement learning
    - User needs documentation or guides on a specific topic
    - User asks questions like "where can I learn more about X?"
    
    Input:
    - query: The search query (e.g., "Python machine learning tutorials")
    - max_results: Number of results to return (default 5)
    
    Returns: A list of relevant resources with titles, URLs, and descriptions.
    """
    args_schema: Type[BaseModel] = ResourceSearchInput

    tavily_api_key: Optional[str] = Field(default=None, exclude=True)
    use_tavily: bool = Field(default=False, exclude=True)

    def __init__(self):
        super().__init__()
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.use_tavily = bool(self.tavily_api_key)

    def _run(self, query: str, max_results: int = 5) -> str:
        """Search for learning resources"""

        try:
            if self.use_tavily:
                resources = self._search_with_tavily(query, max_results)
            else:
                resources = self._search_with_duckduckgo(query, max_results)

            result = ResourceSearchResult(query=query, resources=resources)

            return self._format_results(result)

        except Exception as e:
            return f"Error searching for resources: {str(e)}"

    def _search_with_tavily(self, query: str, max_results: int) -> List[ResourceLink]:
        """Search using Tavily API"""
        url = "https://api.tavily.com/search"

        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_domains": [
                "github.com",
                "stackoverflow.com",
                "medium.com",
                "towardsdatascience.com",
                "dev.to",
                "youtube.com",
                "coursera.org",
                "udemy.com",
                "docs.python.org",
                "tensorflow.org",
                "pytorch.org",
            ],
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        resources = []
        for result in data.get("results", [])[:max_results]:
            resources.append(
                ResourceLink(
                    title=result.get("title", "Untitled"),
                    url=result.get("url", ""),
                    description=result.get("content", "")[:200],
                    relevance_score=result.get("score", 0.5),
                )
            )

        return resources

    def _search_with_duckduckgo(
        self, query: str, max_results: int
    ) -> List[ResourceLink]:
        """Fallback search using DuckDuckGo (no API key required)"""
        try:
            from ddgs import DDGS

            ddgs = DDGS()
            results = ddgs.text(
                f"{query} tutorial guide documentation", max_results=max_results
            )

            resources = []
            for result in results:
                resources.append(
                    ResourceLink(
                        title=result.get("title", "Untitled"),
                        url=result.get("href", result.get("link", "")),
                        description=result.get("body", "")[:200],
                        relevance_score=0.7,
                    )
                )

            return resources

        except ImportError:
            return self._get_fallback_resources(query)

    def _get_fallback_resources(self, query: str) -> List[ResourceLink]:
        """Curated fallback resources when APIs are unavailable"""

        query_lower = query.lower()

        if "python" in query_lower:
            return [
                ResourceLink(
                    title="Official Python Tutorial",
                    url="https://docs.python.org/3/tutorial/",
                    description="Comprehensive guide to Python from python.org",
                ),
                ResourceLink(
                    title="Real Python Tutorials",
                    url="https://realpython.com/",
                    description="In-depth Python tutorials and articles",
                ),
                ResourceLink(
                    title="Python on W3Schools",
                    url="https://www.w3schools.com/python/",
                    description="Interactive Python tutorial with examples",
                ),
            ]

        elif "machine learning" in query_lower or "ml" in query_lower:
            return [
                ResourceLink(
                    title="Machine Learning Crash Course",
                    url="https://developers.google.com/machine-learning/crash-course",
                    description="Google's fast-paced, practical introduction to ML",
                ),
                ResourceLink(
                    title="Scikit-learn Documentation",
                    url="https://scikit-learn.org/stable/",
                    description="Official scikit-learn user guide and tutorials",
                ),
                ResourceLink(
                    title="Towards Data Science",
                    url="https://towardsdatascience.com/",
                    description="Medium publication with ML articles and tutorials",
                ),
            ]

        elif "javascript" in query_lower or "js" in query_lower:
            return [
                ResourceLink(
                    title="MDN JavaScript Guide",
                    url="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
                    description="Comprehensive JavaScript documentation",
                ),
                ResourceLink(
                    title="JavaScript.info",
                    url="https://javascript.info/",
                    description="Modern JavaScript tutorial from basics to advanced",
                ),
                ResourceLink(
                    title="freeCodeCamp JavaScript",
                    url="https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/",
                    description="Interactive JavaScript curriculum",
                ),
            ]

        else:
            return [
                ResourceLink(
                    title=f"{query} - Khan Academy",
                    url=f"https://www.khanacademy.org/search?page_search_query={query.replace(' ', '+')}",
                    description="Free online courses and lessons",
                ),
                ResourceLink(
                    title=f"{query} - Coursera",
                    url=f"https://www.coursera.org/search?query={query.replace(' ', '%20')}",
                    description="Online courses from top universities",
                ),
                ResourceLink(
                    title=f"{query} - YouTube",
                    url=f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+tutorial",
                    description="Video tutorials and explanations",
                ),
            ]

    def _format_results(self, result: ResourceSearchResult) -> str:
        """Format search results for agent consumption"""

        if not result.resources:
            return f"No resources found for query: '{result.query}'"

        output = [
            f"Found {len(result.resources)} learning resources for: '{result.query}'",
            f"Search performed at: {result.search_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "\n" + "=" * 60 + "\n",
        ]

        for idx, resource in enumerate(result.resources, 1):
            output.append(f"{idx}. {resource.title}")
            output.append(f"   URL: {resource.url}")
            if resource.description:
                output.append(f"   Description: {resource.description}")
            output.append(f"   Relevance: {'*' * int(resource.relevance_score * 5)}")
            output.append("")

        output.append("=" * 60)
        output.append(
            "\nPresent these resources to the user in a friendly, helpful way."
        )

        return "\n".join(output)
