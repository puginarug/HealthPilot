"""MCP server for web search tools.

Provides access to academic web search tools via Tavily API
for credible health, nutrition, exercise, and wellbeing information.
"""

from __future__ import annotations

from agents.tools.web_search_tools import (
    lookup_food_nutrients,
    search_dietary_research,
    search_exercise_guidance,
    search_nutrition_knowledge,
    search_wellbeing_research,
)


class WebSearchServer:
    """MCP server for academic health web search tools.

    Provides 5 tools that search only credible academic and medical sources:
    - search_nutrition_knowledge: General nutrition queries
    - lookup_food_nutrients: Specific food nutrition data
    - search_dietary_research: Peer-reviewed diet research
    - search_exercise_guidance: Exercise and fitness guidance
    - search_wellbeing_research: Sleep, stress, and mental health research
    """

    name = "web-search"
    description = "Web search for credible academic health information"

    @staticmethod
    def get_tools() -> list:
        """Return all web search tools.

        Returns:
            List of 5 web search tool functions.
        """
        return [
            search_nutrition_knowledge,
            lookup_food_nutrients,
            search_dietary_research,
            search_exercise_guidance,
            search_wellbeing_research,
        ]


# Singleton instance for registry
web_search_server = WebSearchServer()
