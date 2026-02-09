"""Workout plan exporter - export workout plans to various formats.

Supports JSON, CSV, Markdown, and iCalendar formats following the meal planner pattern.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date, datetime, timedelta
from io import StringIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workout_planning.generator import WorkoutPlan

logger = logging.getLogger(__name__)


class WorkoutPlanExporter:
    """Export workout plans to various formats."""

    def to_json(self, workout_plan: WorkoutPlan) -> str:
        """Export workout plan as JSON.

        Args:
            workout_plan: WorkoutPlan to export

        Returns:
            JSON string with full workout plan data
        """
        return json.dumps(workout_plan.to_dict(), indent=2)

    def to_csv(self, workout_plan: WorkoutPlan) -> str:
        """Export exercise list as CSV.

        Args:
            workout_plan: WorkoutPlan to export

        Returns:
            CSV string with exercise list
        """
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Week",
            "Day",
            "Focus",
            "Exercise",
            "Sets",
            "Reps",
            "Rest (sec)",
            "Tempo",
            "Equipment",
            "Muscle Groups",
            "Notes",
        ])

        # Write exercises
        for week_idx, week in enumerate(workout_plan.weeks, 1):
            for session in week:
                for ex in session.exercises:
                    writer.writerow([
                        f"Week {week_idx}",
                        session.day_name,
                        session.focus,
                        ex.name,
                        ex.sets,
                        ex.reps,
                        ex.rest_seconds,
                        ex.tempo or "",
                        ", ".join(ex.equipment),
                        ", ".join(ex.muscle_groups),
                        " | ".join(ex.notes),
                    ])

        return output.getvalue()

    def to_markdown(self, workout_plan: WorkoutPlan) -> str:
        """Export workout plan as formatted Markdown.

        Args:
            workout_plan: WorkoutPlan to export

        Returns:
            Markdown-formatted workout plan
        """
        lines = [
            f"# {len(workout_plan.weeks)}-Week Workout Plan",
            f"",
            f"**Fitness Level:** {workout_plan.fitness_level.capitalize()}",
            f"**Goals:** {', '.join(workout_plan.goals)}",
            f"**Frequency:** {workout_plan.days_per_week} days/week",
            f"**Session Duration:** {workout_plan.session_duration_min} minutes",
            f"**Equipment:** {', '.join(workout_plan.equipment) if workout_plan.equipment else 'Bodyweight only'}",
        ]

        if workout_plan.restrictions:
            lines.append(f"**Restrictions:** {', '.join(workout_plan.restrictions)}")

        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

        # Export each week
        for week_idx, week in enumerate(workout_plan.weeks, 1):
            lines.append(f"## Week {week_idx}")
            lines.append(f"")

            for session in week:
                lines.append(f"### {session.day_name}: {session.focus}")
                lines.append(f"")
                lines.append(f"**Duration:** ~{session.total_duration_min} minutes | **Total Sets:** {session.total_sets}")
                lines.append(f"")

                # Warmup
                lines.append(f"#### 🔥 Warmup")
                for note in session.warmup_notes:
                    lines.append(f"- {note}")
                lines.append(f"")

                # Exercises
                lines.append(f"#### 💪 Exercises")
                lines.append(f"")

                for ex in session.exercises:
                    lines.append(f"**{ex.name}** ({ex.description})")
                    lines.append(f"- **Sets × Reps:** {ex.sets} × {ex.reps}")
                    lines.append(f"- **Rest:** {ex.rest_seconds}s")
                    if ex.tempo:
                        lines.append(f"- **Tempo:** {ex.tempo}")
                    lines.append(f"- **Equipment:** {', '.join(ex.equipment)}")
                    lines.append(f"- **Muscle Groups:** {', '.join(ex.muscle_groups)}")
                    if ex.notes:
                        lines.append(f"- **Form Notes:**")
                        for note in ex.notes:
                            lines.append(f"  - {note}")
                    lines.append(f"")

                # Cooldown
                lines.append(f"#### 🧘 Cooldown")
                for note in session.cooldown_notes:
                    lines.append(f"- {note}")
                lines.append(f"")
                lines.append(f"---")
                lines.append(f"")

        lines.append(f"")
        lines.append(f"*Generated by HealthPilot AI Health Assistant*")

        return "\n".join(lines)

    def to_icalendar(
        self,
        workout_plan: WorkoutPlan,
        start_date: date,
        preferred_times: dict[str, str],
        timezone: str = "UTC",
    ) -> str:
        """Export workout plan as iCalendar (.ics) file.

        Args:
            workout_plan: WorkoutPlan to export
            start_date: When to start the workout plan
            preferred_times: Dict mapping day names to preferred times (HH:MM format)
            timezone: User's timezone (IANA format)

        Returns:
            iCalendar format string compatible with Google Calendar, Outlook, etc.
        """
        try:
            from icalendar import Calendar, Event
            from zoneinfo import ZoneInfo
        except ImportError:
            logger.error("icalendar library not installed. Install with: pip install icalendar")
            raise ImportError("icalendar library required for iCalendar export")

        cal = Calendar()
        cal.add("prodid", "-//HealthPilot Workout Planner//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")
        cal.add("x-wr-calname", "HealthPilot Workout Plan")
        cal.add("x-wr-timezone", timezone)

        tz = ZoneInfo(timezone)
        session_idx = 0

        for week_idx, week in enumerate(workout_plan.weeks, 1):
            for session in week:
                # Calculate session date
                session_date = start_date + timedelta(days=session_idx)
                day_name = session_date.strftime("%A")

                # Get preferred time or default to 7 AM
                time_str = preferred_times.get(day_name, "07:00")
                try:
                    hour, minute = map(int, time_str.split(":"))
                except (ValueError, AttributeError):
                    hour, minute = 7, 0  # Fallback

                # Create timezone-aware datetime
                start_dt = datetime(
                    session_date.year,
                    session_date.month,
                    session_date.day,
                    hour,
                    minute,
                    tzinfo=tz,
                )
                end_dt = start_dt + timedelta(minutes=session.total_duration_min)

                # Create calendar event
                event = Event()
                event.add("summary", f"💪 Workout: {session.focus}")
                event.add("dtstart", start_dt)
                event.add("dtend", end_dt)
                event.add("dtstamp", datetime.now(tz=tz))
                event.add("location", "Gym")
                event.add("description", self._format_workout_description(session, week_idx))
                event.add("status", "CONFIRMED")
                event.add("transp", "OPAQUE")  # Mark as busy

                cal.add_component(event)
                session_idx += 1

        return cal.to_ical().decode("utf-8")

    def _format_workout_description(self, session: Any, week_idx: int) -> str:
        """Format workout session as detailed calendar event description.

        Args:
            session: WorkoutSession to format
            week_idx: Week number

        Returns:
            Formatted description string
        """
        lines = [
            f"Week {week_idx} - {session.day_name}",
            f"Focus: {session.focus}",
            f"Duration: ~{session.total_duration_min} minutes",
            f"Total Sets: {session.total_sets}",
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
        lines.append("Generated by HealthPilot AI")

        return "\n".join(lines)
