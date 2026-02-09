"""Calendar integration for workout scheduling with proper timezone handling.

Fixes timezone bugs from chat page implementation and enables bulk workout scheduling.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workout_planning.generator import WorkoutSession

logger = logging.getLogger(__name__)


def schedule_workouts_bulk(
    workout_sessions: list[WorkoutSession],
    start_date: date,
    preferred_times: dict[str, str],
    user_timezone: str = "UTC",
) -> tuple[bool, str, list[dict]]:
    """Schedule multiple workout sessions to Google Calendar with proper timezone handling.

    Key fixes from buggy chat implementation:
    1. Uses ZoneInfo for timezone-aware datetimes
    2. Allows user to customize times per day
    3. Bulk schedules all workouts at once
    4. Uses user's timezone from profile.json

    Args:
        workout_sessions: List of WorkoutSession objects to schedule
        start_date: Date to start the workout plan
        preferred_times: Dict mapping day names to preferred times (HH:MM format)
                        Example: {"Monday": "07:00", "Wednesday": "18:00"}
        user_timezone: User's timezone in IANA format (e.g., "America/New_York")

    Returns:
        Tuple of (success: bool, message: str, list of created event dicts)
    """
    try:
        from integrations.google_calendar import GoogleCalendarClient
        from zoneinfo import ZoneInfo
    except ImportError as e:
        logger.error("Required dependency not available: %s", e)
        return False, f"Missing dependency: {e}", []

    try:
        calendar_client = GoogleCalendarClient()
        created_events = []

        # Parse timezone
        try:
            tz = ZoneInfo(user_timezone)
        except Exception as e:
            logger.warning("Invalid timezone %s, falling back to UTC: %s", user_timezone, e)
            tz = ZoneInfo("UTC")

        for i, session in enumerate(workout_sessions):
            # Calculate session date
            session_date = start_date + timedelta(days=i)
            day_name = session_date.strftime("%A")

            # Get preferred time or default to 7 AM
            time_str = preferred_times.get(day_name, "07:00")
            try:
                hour, minute = map(int, time_str.split(":"))
                # Validate time
                if not (0 <= hour < 24 and 0 <= minute < 60):
                    hour, minute = 7, 0  # Fallback
            except (ValueError, AttributeError):
                hour, minute = 7, 0  # Fallback

            # ✅ Create timezone-aware datetime
            start_time = datetime(
                session_date.year,
                session_date.month,
                session_date.day,
                hour,
                minute,
                tzinfo=tz,
            )

            # ✅ ISO format includes timezone: "2026-02-10T07:00:00+02:00"
            start_iso = start_time.isoformat()

            # Create calendar event
            event = calendar_client.create_event(
                title=f"💪 Workout: {session.focus}",
                start_time=start_iso,
                duration_minutes=session.total_duration_min,
                description=_format_workout_description(session),
            )

            if event:
                created_events.append({
                    "id": event.get("id"),
                    "session": session.day_name,
                    "time": start_time,
                    "html_link": event.get("htmlLink"),
                })
            else:
                logger.warning("Failed to create calendar event for session: %s", session.day_name)

        if created_events:
            return True, f"Scheduled {len(created_events)} workouts successfully", created_events
        else:
            return False, "No events were created", []

    except FileNotFoundError:
        return False, "Google Calendar not configured. Set up credentials first.", []
    except Exception as e:
        logger.error("Calendar scheduling failed: %s", e, exc_info=True)
        return False, f"Error: {str(e)}", []


def _format_workout_description(session: WorkoutSession) -> str:
    """Format workout session as detailed calendar event description.

    Args:
        session: WorkoutSession to format

    Returns:
        Formatted description string for calendar event
    """
    lines = [
        f"Workout: {session.focus}",
        f"Duration: ~{session.total_duration_min} minutes",
        f"Total Sets: {session.total_sets}",
        f"Muscle Groups: {', '.join(session.muscle_groups_targeted)}",
        f"",
        "WARMUP:",
    ]

    for note in session.warmup_notes:
        lines.append(f"  • {note}")

    lines.append("")
    lines.append("EXERCISES:")

    for ex in session.exercises:
        lines.append(f"  • {ex.name}: {ex.sets} × {ex.reps} (rest {ex.rest_seconds}s)")
        if ex.notes:
            lines.append(f"    Form: {ex.notes[0]}")

    lines.append("")
    lines.append("COOLDOWN:")

    for note in session.cooldown_notes:
        lines.append(f"  • {note}")

    lines.append("")
    lines.append("---")
    lines.append("Generated by HealthPilot AI Health Assistant")
    lines.append("Track your progress and adjust weights as needed!")

    return "\n".join(lines)


def get_preferred_time_defaults() -> dict[str, str]:
    """Get default preferred workout times for each day.

    Returns:
        Dict mapping day names to default times (HH:MM format)
    """
    return {
        "Monday": "07:00",
        "Tuesday": "07:00",
        "Wednesday": "07:00",
        "Thursday": "07:00",
        "Friday": "07:00",
        "Saturday": "09:00",  # Weekend: later start
        "Sunday": "09:00",
    }
