"""MCP Server for nutrition and dietary tools.

Provides RAG-powered nutrition knowledge access via USDA and PubMed.
"""

from __future__ import annotations

import logging

from agents.tools.nutrition_tools import (
    export_meal_plan_json,
    generate_meal_plan,
    lookup_food_nutrients,
    search_dietary_research,
    search_nutrition_knowledge,
)

logger = logging.getLogger(__name__)


class NutritionServer:
    """MCP server providing nutrition and dietary information.

    Tools:
    - search_nutrition_knowledge: Search USDA + PubMed
    - lookup_food_nutrients: Get specific food data
    - search_dietary_research: Query research abstracts
    - generate_meal_plan: Create personalized meal plans
    - export_meal_plan_json: Export meal plan to file
    """

    name = "nutrition"
    description = "Access nutritional data from USDA FoodData Central and PubMed research"

    @staticmethod
    def get_tools() -> list:
        """Return all tools provided by this server."""
        return [
            search_nutrition_knowledge,
            lookup_food_nutrients,
            search_dietary_research,
            generate_meal_plan,
            export_meal_plan_json,
        ]

    @staticmethod
    def get_tool_names() -> list[str]:
        """Return names of all tools."""
        return [tool.name for tool in NutritionServer.get_tools()]


# Server instance
nutrition_server = NutritionServer()
