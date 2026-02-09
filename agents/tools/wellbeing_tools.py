"""Wellbeing agent tools.

Tools for sleep analysis and schedule balance assessment.
"""

from __future__ import annotations

import logging

import pandas as pd
from langchain_core.tools import tool

from analytics.data_pipeline import HealthDataLoader
from analytics.health_metrics import HealthMetrics

logger = logging.getLogger(__name__)


@tool
def analyze_sleep_data(period_days: int = 30) -> str:
    """Analyze sleep data for quality, consistency, and patterns.

    Args:
        period_days: Number of recent days to analyze (default 30).

    Returns:
        Sleep summary including duration, stages, consistency, and
        social jet lag metrics.
    """
    try:
        loader = HealthDataLoader()
        df = loader.load_sleep()

        # Filter to period
        if period_days < len(df):
            cutoff = df["date"].max() - pd.Timedelta(days=period_days)
            df = df[df["date"] >= cutoff]

        metrics = HealthMetrics()
        summary = metrics.compute_sleep_summary(df)

        lines = [
            f"Sleep Summary (last {len(df)} nights):",
            f"  Average Duration: {summary.avg_duration_hours:.1f} hours",
            f"  Consistency: ±{summary.bedtime_consistency * 60:.0f} min std dev",
            f"  Weekend Shift: {summary.weekend_shift_hours:+.1f} hours (social jet lag)",
            "  Sleep Stages:",
            f"    Deep: {summary.avg_deep_sleep_pct:.1f}%",
            f"    REM: {summary.avg_rem_pct:.1f}%",
            f"    Light: {summary.avg_light_sleep_pct:.1f}%",
        ]

        # Recommendations
        if summary.avg_duration_hours < 7.0:
            lines.append("⚠️  Duration below 7h. Consider earlier bedtime.")
        elif 7.0 <= summary.avg_duration_hours <= 9.0:
            lines.append("✅ Healthy sleep duration.")

        if summary.bedtime_consistency > 1.0:
            lines.append("⚠️  Inconsistent bedtime. Aim for same time ±30min.")

        if abs(summary.weekend_shift_hours) > 1.0:
            lines.append(f"⚠️  Social jet lag detected ({summary.weekend_shift_hours:+.1f}h weekend shift).")

        logger.info("Analyzed sleep data: %d nights", len(df))
        return "\n".join(lines)

    except FileNotFoundError:
        return "Sleep data not found. Ensure data/sample/sleep.csv exists."
    except Exception as e:
        logger.error("Sleep analysis failed: %s", e)
        return f"Error analyzing sleep: {e}"


@tool
def analyze_schedule_balance(days_ahead: int = 7) -> str:
    """Analyze schedule balance and identify over-scheduling (placeholder).

    Args:
        days_ahead: Number of days to analyze (default 7).

    Returns:
        Schedule balance metrics and recommendations.
    """
    return (
        f"Schedule balance analysis requires Google Calendar integration (not yet implemented). "
        f"Would analyze the next {days_ahead} days for:\n"
        f"  - Meeting density\n"
        f"  - Free time blocks\n"
        f"  - Work-life balance ratios\n"
        f"  - Social and creative time allocation"
    )


@tool
def suggest_wellness_activities(available_minutes: int = 30, stress_level: str = "moderate") -> str:
    """Suggest wellness activities based on available time and stress level.

    Args:
        available_minutes: How much time is available (default 30).
        stress_level: Current stress level ("low", "moderate", or "high").

    Returns:
        Personalized wellness activity suggestions.
    """
    activities = {
        "high": {
            "short": ["Deep breathing exercises (5 min)", "Progressive muscle relaxation", "Mindfulness meditation"],
            "medium": ["Guided meditation session", "Gentle yoga", "Nature walk"],
            "long": ["Restorative yoga class", "Long nature hike", "Spa/self-care session"],
        },
        "moderate": {
            "short": ["Quick walk", "Desk stretches", "Gratitude journaling"],
            "medium": ["Moderate exercise", "Creative hobby time", "Social call with friend"],
            "long": ["Exercise class", "Creative project work", "Social outing"],
        },
        "low": {
            "short": ["Quick energizing walk", "Learning something new", "Planning/organizing"],
            "medium": ["Challenging workout", "Skill practice", "Social engagement"],
            "long": ["Intense workout", "Major creative project", "Adventure activity"],
        },
    }

    level = stress_level.lower()
    if level not in activities:
        level = "moderate"

    if available_minutes < 15:
        category = "short"
    elif available_minutes < 45:
        category = "medium"
    else:
        category = "long"

    suggestions = activities[level][category]

    lines = [
        f"Wellness Suggestions ({level.capitalize()} stress, {available_minutes} min available):",
        "",
    ]
    for i, activity in enumerate(suggestions, 1):
        lines.append(f"  {i}. {activity}")

    lines.append("")
    lines.append("Remember: Consistency matters more than duration. Even 5 minutes helps.")

    logger.info("Generated wellness suggestions for %s stress, %d min", level, available_minutes)
    return "\n".join(lines)
