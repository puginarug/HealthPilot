"""Exercise agent tools.

Tools for analyzing activity data and (placeholder for) Google Calendar integration.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pandas as pd
from langchain_core.tools import tool

from analytics.data_pipeline import HealthDataLoader
from analytics.health_metrics import HealthMetrics

logger = logging.getLogger(__name__)


@tool
def analyze_activity_data(period_days: int = 30) -> str:
    """Analyze activity data from wearable device for a given period.

    Args:
        period_days: Number of recent days to analyze (default 30).

    Returns:
        Activity summary including average steps, trend analysis,
        weekday vs weekend patterns, and recommendations.
    """
    try:
        loader = HealthDataLoader()
        df = loader.load_activity()

        # Filter to period
        if period_days < len(df):
            cutoff = df["date"].max() - pd.Timedelta(days=period_days)
            df = df[df["date"] >= cutoff]

        metrics = HealthMetrics()
        summary = metrics.compute_activity_summary(df)

        # Format output
        lines = [
            f"Activity Summary (last {len(df)} days):",
            f"  Average Steps: {summary.mean_steps:,.0f}/day",
            f"  Total Distance: {summary.total_distance_km:.1f} km",
            f"  Total Active Minutes: {summary.total_active_minutes:,}",
            f"  Avg Calories: {summary.avg_daily_calories:,.0f} kcal/day",
            f"  Trend: {summary.trend_slope:+.0f} steps/day (p={summary.trend_pvalue:.3f})",
            f"  Weekday Avg: {summary.weekday_avg_steps:,.0f} steps",
            f"  Weekend Avg: {summary.weekend_avg_steps:,.0f} steps",
        ]

        # Interpretation
        if summary.trend_slope > 20 and summary.trend_pvalue < 0.05:
            lines.append("📈 Positive trend: Activity is improving.")
        elif summary.trend_slope < -20 and summary.trend_pvalue < 0.05:
            lines.append("📉 Negative trend: Activity is declining.")
        else:
            lines.append("➡️  Stable: No significant trend.")

        logger.info("Analyzed activity data: %d days", len(df))
        return "\n".join(lines)

    except FileNotFoundError:
        return "Activity data not found. Ensure data/sample/daily_activity.csv exists."
    except Exception as e:
        logger.error("Activity analysis failed: %s", e)
        return f"Error analyzing activity: {e}"


@tool
def analyze_heart_rate_data(period_days: int = 7) -> str:
    """Analyze heart rate data for cardiovascular fitness insights.

    Args:
        period_days: Number of recent days to analyze (default 7).

    Returns:
        Heart rate summary including resting HR, zone distribution,
        and circadian patterns.
    """
    try:
        loader = HealthDataLoader()
        df = loader.load_heart_rate()

        # Filter to period
        if period_days * 288 < len(df):  # 288 = 5-min intervals per day
            cutoff = df["timestamp"].max() - pd.Timedelta(days=period_days)
            df = df[df["timestamp"] >= cutoff]

        metrics = HealthMetrics()
        summary = metrics.compute_hr_summary(df)

        lines = [
            f"Heart Rate Summary (last {len(df):,} measurements):",
            f"  Resting HR: {summary.resting_hr_mean:.0f} ± {summary.resting_hr_std:.0f} bpm",
            f"  Max HR Observed: {summary.max_hr_observed} bpm",
            "  Time in Zones:",
            f"    Resting (<70): {summary.time_in_zones['resting']:.1f}%",
            f"    Light (70-100): {summary.time_in_zones['light']:.1f}%",
            f"    Moderate (100-140): {summary.time_in_zones['moderate']:.1f}%",
            f"    Vigorous (>140): {summary.time_in_zones['vigorous']:.1f}%",
        ]

        # Fitness interpretation
        if summary.resting_hr_mean < 60:
            lines.append("✅ Excellent cardiovascular fitness (athlete-level resting HR).")
        elif summary.resting_hr_mean <= 80:
            lines.append("✅ Normal resting HR. Regular exercise can lower it further.")
        else:
            lines.append("⚠️  Elevated resting HR. Consider stress management and hydration.")

        logger.info("Analyzed HR data: %d measurements", len(df))
        return "\n".join(lines)

    except FileNotFoundError:
        return "Heart rate data not found. Ensure data/sample/heart_rate.csv exists."
    except Exception as e:
        logger.error("HR analysis failed: %s", e)
        return f"Error analyzing heart rate: {e}"


@tool
def get_exercise_recommendations(fitness_level: str = "intermediate", goals: str = "") -> str:
    """Get personalized exercise recommendations based on fitness level and goals.

    Args:
        fitness_level: Current fitness level ("beginner", "intermediate", or "advanced").
        goals: Fitness goals (e.g., "build strength", "improve endurance", "lose weight").

    Returns:
        Evidence-based exercise recommendations tailored to the user.
    """
    # Placeholder recommendations (could be enhanced with RAG in future)
    recommendations = {
        "beginner": {
            "frequency": "3-4 days/week",
            "duration": "20-30 minutes",
            "types": ["Walking", "Bodyweight exercises", "Light cycling"],
            "advice": "Focus on building a consistent habit. Start with low intensity and gradually increase.",
        },
        "intermediate": {
            "frequency": "4-5 days/week",
            "duration": "30-45 minutes",
            "types": ["Running", "Resistance training", "HIIT", "Swimming"],
            "advice": "Mix cardio and strength training. Challenge yourself with progressive overload.",
        },
        "advanced": {
            "frequency": "5-6 days/week",
            "duration": "45-90 minutes",
            "types": ["Advanced strength training", "Long-distance running", "Sport-specific training"],
            "advice": "Periodize your training. Focus on recovery and nutrition to support high volume.",
        },
    }

    level = fitness_level.lower()
    if level not in recommendations:
        level = "intermediate"

    rec = recommendations[level]

    lines = [
        f"Exercise Recommendations ({level.capitalize()} Level):",
        f"  Frequency: {rec['frequency']}",
        f"  Duration: {rec['duration']}",
        f"  Recommended Activities: {', '.join(rec['types'])}",
        f"  Advice: {rec['advice']}",
    ]

    if goals:
        lines.append(f"\nFor your goal of '{goals}', prioritize exercises that align with this objective.")

    logger.info("Generated exercise recommendations for %s level", level)
    return "\n".join(lines)


@tool
def read_google_calendar(days_ahead: int = 7) -> str:
    """Read upcoming Google Calendar events.

    Fetches events from your Google Calendar to check for scheduling conflicts
    or to understand your weekly schedule.

    Args:
        days_ahead: Number of days to look ahead (default 7).

    Returns:
        Formatted list of upcoming events or error message.
    """
    try:
        from integrations.google_calendar import get_calendar_client

        client = get_calendar_client()
        events = client.list_events(days_ahead=days_ahead)

        if not events:
            return f"No upcoming events found in the next {days_ahead} days."

        lines = [f"Upcoming Events (next {days_ahead} days):"]
        for event in events:
            start = event["start"][:16]  # YYYY-MM-DDTHH:MM
            lines.append(f"  • {event['summary']} - {start}")
            if event.get("description"):
                lines.append(f"    {event['description'][:60]}")

        logger.info("Retrieved %d calendar events", len(events))
        return "\n".join(lines)

    except FileNotFoundError:
        return (
            "Google Calendar not configured. To enable:\n"
            "1. Download OAuth credentials from Google Cloud Console\n"
            "2. Save as credentials/google_credentials.json\n"
            "3. Run the app and authorize access"
        )
    except Exception as e:
        logger.error("Failed to read calendar: %s", e)
        return f"Error reading calendar: {e}"


@tool
def create_calendar_event(title: str, start_time: str, duration_minutes: int = 60) -> str:
    """Create a Google Calendar event for workouts or wellness activities.

    Schedules an event in your Google Calendar. Use this to block time
    for exercise, meal prep, or other health activities.

    Args:
        title: Event title (e.g., "Morning Run", "Gym - Upper Body", "Meal Prep").
        start_time: Start time in ISO format (e.g., "2026-02-10T07:00:00").
        duration_minutes: Event duration in minutes (default 60).

    Returns:
        Confirmation with event link or error message.
    """
    try:
        from integrations.google_calendar import get_calendar_client

        client = get_calendar_client()
        result = client.create_event(
            title=title,
            start_time=start_time,
            duration_minutes=duration_minutes,
            description=f"Created by HealthPilot AI Assistant",
        )

        if result:
            return (
                f"✅ Created event: '{title}' at {start_time} ({duration_minutes} min)\n"
                f"Event ID: {result['id']}\n"
                f"Link: {result.get('link', 'N/A')}"
            )
        else:
            return "Failed to create event. Check logs for details."

    except FileNotFoundError:
        return (
            "Google Calendar not configured. To enable:\n"
            "1. Download OAuth credentials from Google Cloud Console\n"
            "2. Save as credentials/google_credentials.json\n"
            "3. Run the app and authorize access"
        )
    except Exception as e:
        logger.error("Failed to create calendar event: %s", e)
        return f"Error creating event: {e}"
