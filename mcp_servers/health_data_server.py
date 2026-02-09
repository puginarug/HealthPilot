"""MCP Server for health data analysis tools.

Provides tools for analyzing activity, heart rate, and sleep data.
"""

from __future__ import annotations

import logging

from agents.tools.exercise_tools import (
    analyze_activity_data,
    analyze_heart_rate_data,
)
from agents.tools.wellbeing_tools import analyze_sleep_data

logger = logging.getLogger(__name__)


class HealthDataServer:
    """MCP server providing health data analysis capabilities.

    Tools:
    - analyze_activity_data: Daily steps, calories, trends
    - analyze_heart_rate_data: HR zones, resting HR
    - analyze_sleep_data: Sleep quality, consistency
    """

    name = "health-data"
    description = "Analyze wearable health data (activity, heart rate, sleep)"

    @staticmethod
    def get_tools() -> list:
        """Return all tools provided by this server."""
        return [
            analyze_activity_data,
            analyze_heart_rate_data,
            analyze_sleep_data,
        ]

    @staticmethod
    def get_tool_names() -> list[str]:
        """Return names of all tools."""
        return [tool.name for tool in HealthDataServer.get_tools()]


# Server instance
health_data_server = HealthDataServer()
