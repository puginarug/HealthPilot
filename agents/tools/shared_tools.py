"""Shared tools used across multiple agents.

Provides user profile management and common utilities.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_core.tools import tool

from config import get_settings

logger = logging.getLogger(__name__)


@tool
def get_user_profile() -> str:
    """Get the user's health profile including goals, preferences, and restrictions.

    Returns:
        JSON string with user profile data including dietary preferences,
        fitness goals, calorie targets, and equipment available.
    """
    settings = get_settings()
    profile_path = settings.user_profile_path

    if not profile_path.exists():
        return json.dumps({
            "error": "User profile not found",
            "message": "Create data/user_profile.json to personalize recommendations",
        })

    try:
        with open(profile_path) as f:
            profile = json.load(f)
        logger.info("Loaded user profile: %s", profile.get("name", "Unknown"))
        return json.dumps(profile, indent=2)
    except Exception as e:
        logger.error("Failed to load user profile: %s", e)
        return json.dumps({"error": str(e)})


@tool
def update_user_profile(updates: dict) -> str:
    """Update fields in the user's health profile.

    Args:
        updates: Dictionary of fields to update (e.g., {"daily_step_goal": 12000}).

    Returns:
        Confirmation message with updated profile.
    """
    settings = get_settings()
    profile_path = settings.user_profile_path

    if not profile_path.exists():
        return "Error: User profile not found. Cannot update."

    try:
        with open(profile_path) as f:
            profile = json.load(f)

        profile.update(updates)

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=4)

        logger.info("Updated user profile: %s", list(updates.keys()))
        return f"Profile updated successfully. Changed fields: {', '.join(updates.keys())}"

    except Exception as e:
        logger.error("Failed to update profile: %s", e)
        return f"Error updating profile: {e}"
