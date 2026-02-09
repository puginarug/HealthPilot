"""MCP Server for wellness and lifestyle tools.

Provides wellness activity suggestions and schedule management.
"""

from __future__ import annotations

import logging

from agents.tools.exercise_tools import (
    create_calendar_event,
    get_exercise_recommendations,
    read_google_calendar,
)
from agents.tools.shared_tools import get_user_profile, update_user_profile
from agents.tools.wellbeing_tools import (
    analyze_schedule_balance,
    suggest_wellness_activities,
)

logger = logging.getLogger(__name__)


class WellnessServer:
    """MCP server providing wellness and lifestyle management.

    Tools:
    - suggest_wellness_activities: Activity recommendations
    - analyze_schedule_balance: Work-life balance analysis
    - get_exercise_recommendations: Workout suggestions
    - read_google_calendar: Fetch calendar events
    - create_calendar_event: Schedule activities
    - get_user_profile: Read user preferences
    - update_user_profile: Update user settings
    """

    name = "wellness"
    description = "Wellness activities, schedule management, and user preferences"

    @staticmethod
    def get_tools() -> list:
        """Return all tools provided by this server."""
        return [
            suggest_wellness_activities,
            analyze_schedule_balance,
            get_exercise_recommendations,
            read_google_calendar,
            create_calendar_event,
            get_user_profile,
            update_user_profile,
        ]

    @staticmethod
    def get_tool_names() -> list[str]:
        """Return names of all tools."""
        return [tool.name for tool in WellnessServer.get_tools()]


# Server instance
wellness_server = WellnessServer()
