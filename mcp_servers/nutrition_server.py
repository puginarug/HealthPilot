"""MCP Server for nutrition and dietary tools.

Provides meal planning tools. Web search tools for nutrition knowledge
are now in web_search_server.py.
"""

from __future__ import annotations

import logging

from agents.tools.nutrition_tools import (
    export_meal_plan_json,
    generate_meal_plan,
)

logger = logging.getLogger(__name__)


class NutritionServer:
    """MCP server providing meal planning tools.

    Tools:
    - generate_meal_plan: Create personalized meal plans
    - export_meal_plan_json: Export meal plan to file

    Note: Nutrition knowledge search tools are now in web_search_server.py
    """

    name = "nutrition"
    description = "Generate personalized meal plans with nutritional tracking"

    @staticmethod
    def get_tools() -> list:
        """Return all tools provided by this server."""
        return [
            generate_meal_plan,
            export_meal_plan_json,
        ]

    @staticmethod
    def get_tool_names() -> list[str]:
        """Return names of all tools."""
        return [tool.name for tool in NutritionServer.get_tools()]


# Server instance
nutrition_server = NutritionServer()
