"""Workout Planning page.

Interactive workout plan generation using the workout planning module with LLM-powered suggestions.
Mirrors the meal planner architecture with proper calendar integration.
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from config import get_settings
from workout_planning.calendar_integration import (
    get_preferred_time_defaults,
    schedule_workouts_bulk,
)
from workout_planning.exporter import WorkoutPlanExporter
from workout_planning.generator import WorkoutPlanGenerator

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Workout Planner", page_icon="💪", layout="wide")

settings = get_settings()


def main() -> None:
    """Render the workout planning page."""
    st.header("💪 Workout Planner")

    # Check API key
    if not settings.has_llm_key():
        st.error(
            f"No {settings.llm_provider.upper()} API key found. "
            f"Add your API key to `.env` to use workout planning."
        )
        return

    st.markdown(
        """
        Generate personalized workout plans powered by AI and backed by exercise science principles.
        Includes exercise details, sets/reps, rest periods, and calendar integration.
        """
    )

    # Load user profile
    profile_path = Path("data/user_profile.json")
    profile = None

    if profile_path.exists():
        try:
            with open(profile_path) as f:
                profile = json.load(f)
        except Exception as e:
            logger.error("Failed to load user profile: %s", e)

    # Show recommendations if profile exists
    if profile and "fitness_level" in profile:
        st.markdown("### 💡 Based on Your Profile")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Fitness Level:** {profile['fitness_level'].capitalize()}")
        with col2:
            if "fitness_goals" in profile:
                goals_str = ", ".join(profile["fitness_goals"][:2])
                st.info(f"**Goals:** {goals_str}")
        with col3:
            equipment_count = len(profile.get("available_equipment", []))
            st.info(f"**Equipment:** {equipment_count} items available")

    st.markdown("---")

    # Main configuration
    st.subheader("⚙️ Workout Plan Settings")

    col1, col2 = st.columns(2)

    with col1:
        fitness_level = st.selectbox(
            "Fitness Level",
            ["beginner", "intermediate", "advanced"],
            index=1,  # Default to intermediate
            help="Your current training experience level",
        )

        # Map profile goals to available options
        available_goals = ["strength", "hypertrophy", "endurance", "weight_loss", "flexibility"]
        default_goals = ["strength", "hypertrophy"]

        if profile and "fitness_goals" in profile:
            # Filter profile goals to only include those in available options
            profile_goals = [g for g in profile["fitness_goals"] if g in available_goals]
            if profile_goals:
                default_goals = profile_goals

        goals = st.multiselect(
            "Training Goals",
            available_goals,
            default=default_goals,
            help="Select one or more training goals",
        )

        days_per_week = st.slider(
            "Days Per Week",
            min_value=3,
            max_value=6,
            value=4,
            help="Number of workout days per week",
        )

    with col2:
        session_duration = st.select_slider(
            "Session Duration (minutes)",
            options=[30, 45, 60, 90],
            value=60,
            help="Target duration for each workout session",
        )

        # Equipment options
        available_equipment_options = [
            "bodyweight",
            "dumbbells",
            "barbell",
            "pull-up bar",
            "dip bars",
            "bench",
            "squat rack",
            "cable machine",
            "resistance bands",
            "kettlebells",
        ]
        default_equipment = ["bodyweight", "dumbbells"]

        if profile and "available_equipment" in profile:
            # Filter profile equipment to only include those in available options
            profile_equipment = [e for e in profile["available_equipment"] if e in available_equipment_options]
            if profile_equipment:
                default_equipment = profile_equipment

        equipment = st.multiselect(
            "Available Equipment",
            available_equipment_options,
            default=default_equipment,
            help="Equipment you have access to",
        )

        restrictions = st.text_input(
            "Injuries / Restrictions",
            placeholder="e.g., lower back pain, shoulder injury",
            help="Any injuries or limitations to work around",
        )

        weeks_to_generate = st.slider(
            "Weeks to Generate",
            min_value=1,
            max_value=4,
            value=1,
            help="Number of weeks for the workout plan",
        )

    st.markdown("---")

    # Generate button
    generate_button = st.button(
        "🔄 Generate Workout Plan",
        type="primary",
        use_container_width=True,
    )

    # Generate workout plan
    if generate_button:
        if not goals:
            st.error("Please select at least one training goal.")
            return

        if not equipment:
            equipment = ["bodyweight"]  # Default to bodyweight if nothing selected

        with st.spinner("Generating your personalized workout plan..."):
            try:
                generator = WorkoutPlanGenerator()
                restrictions_list = [r.strip() for r in restrictions.split(",") if r.strip()] if restrictions else []

                workout_plan = generator.generate(
                    weeks=weeks_to_generate,
                    fitness_level=fitness_level,
                    goals=goals,
                    days_per_week=days_per_week,
                    session_duration_min=session_duration,
                    equipment=equipment,
                    restrictions=restrictions_list,
                    user_profile=profile,
                )

                # Store in session state
                st.session_state["workout_plan"] = workout_plan
                st.success(f"✅ Generated {weeks_to_generate}-week workout plan!")

            except Exception as e:
                logger.error("Workout plan generation failed: %s", e)
                st.error(f"Error generating workout plan: {e}")
                return

    # Display workout plan if available
    if "workout_plan" not in st.session_state:
        st.markdown("---")
        st.info("### 👆 Click 'Generate Workout Plan' to get started!")
        return

    workout_plan = st.session_state["workout_plan"]

    st.markdown("---")

    # Main tabs for Workout Plan, Exercise Library, Calendar, and Downloads
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Workout Plan",
        "📚 Exercise Library",
        "📅 Schedule",
        "⬇️ Downloads"
    ])

    # ===== TAB 1: WORKOUT PLAN =====
    with tab1:
        display_workout_plan_tab(workout_plan)

    # ===== TAB 2: EXERCISE LIBRARY =====
    with tab2:
        display_exercise_library_tab(workout_plan)

    # ===== TAB 3: SCHEDULE TO CALENDAR =====
    with tab3:
        display_schedule_tab(workout_plan, profile)

    # ===== TAB 4: DOWNLOADS =====
    with tab4:
        display_downloads_tab(workout_plan, profile)


def display_workout_plan_tab(workout_plan) -> None:
    """Display the workout plan tab with week/day breakdown."""
    st.subheader(f"📅 Your {len(workout_plan.weeks)}-Week Workout Plan")

    st.info(
        f"**Fitness Level:** {workout_plan.fitness_level.capitalize()} | "
        f"**Goals:** {', '.join(workout_plan.goals)} | "
        f"**Frequency:** {workout_plan.days_per_week} days/week | "
        f"**Duration:** {workout_plan.session_duration_min} min/session"
    )

    # Week tabs if multi-week
    if len(workout_plan.weeks) > 1:
        week_tabs = st.tabs([f"Week {i+1}" for i in range(len(workout_plan.weeks))])

        for week_idx, (week_tab, week) in enumerate(zip(week_tabs, workout_plan.weeks)):
            with week_tab:
                display_week(week, week_idx + 1)
    else:
        # Single week - display directly
        display_week(workout_plan.weeks[0], 1)


def display_week(week, week_number: int) -> None:
    """Display a single week with day tabs."""
    st.markdown(f"### Week {week_number}")

    # Day tabs
    day_tabs = st.tabs([session.day_name for session in week])

    for day_tab, session in zip(day_tabs, week):
        with day_tab:
            display_workout_session(session)


def display_workout_session(session) -> None:
    """Display a single workout session with all details."""
    st.markdown(f"### {session.focus}")

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Duration", f"~{session.total_duration_min} min")
    col2.metric("Total Sets", session.total_sets)
    col3.metric("Muscle Groups", ", ".join(session.muscle_groups_targeted[:3]))

    st.markdown("---")

    # Warmup
    st.markdown("#### 🔥 Warmup")
    for note in session.warmup_notes:
        st.markdown(f"- {note}")

    st.markdown("---")

    # Exercises
    st.markdown("#### 💪 Exercises")

    for idx, ex in enumerate(session.exercises, 1):
        with st.expander(f"**{idx}. {ex.name}** - {ex.sets} × {ex.reps}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Description:** {ex.description}")

                if ex.notes:
                    st.markdown("**Form Cues:**")
                    for note in ex.notes:
                        st.markdown(f"  - {note}")

            with col2:
                st.markdown(f"**Rest:** {ex.rest_seconds}s")
                if ex.tempo:
                    st.markdown(f"**Tempo:** {ex.tempo}")
                st.markdown(f"**Equipment:** {', '.join(ex.equipment)}")
                st.markdown(f"**Muscles:** {', '.join(ex.muscle_groups)}")

    st.markdown("---")

    # Cooldown
    st.markdown("#### 🧘 Cooldown")
    for note in session.cooldown_notes:
        st.markdown(f"- {note}")


def display_exercise_library_tab(workout_plan) -> None:
    """Display the exercise library reference tab."""
    from workout_planning.exercise_library import get_exercise_reference

    st.subheader("📚 Exercise Library")
    st.caption("Reference guide for exercises in your workout plan")

    # Collect unique exercises from plan
    all_exercises = set()
    for week in workout_plan.weeks:
        for session in week:
            for ex in session.exercises:
                all_exercises.add(ex.name)

    if not all_exercises:
        st.info("No exercises found in workout plan.")
        return

    # Display exercises alphabetically
    for exercise_name in sorted(all_exercises):
        reference = get_exercise_reference(exercise_name)

        if reference:
            with st.expander(f"**{exercise_name}** ({reference.category.capitalize()})", expanded=False):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Primary Muscles:** {', '.join(reference.primary_muscles)}")
                    if reference.secondary_muscles:
                        st.markdown(f"**Secondary Muscles:** {', '.join(reference.secondary_muscles)}")

                    st.markdown("**Form Cues:**")
                    for cue in reference.form_cues:
                        st.markdown(f"  - {cue}")

                with col2:
                    st.markdown(f"**Difficulty:** {reference.difficulty.capitalize()}")
                    st.markdown(f"**Equipment:** {', '.join(reference.equipment)}")

                if reference.common_mistakes:
                    st.markdown("**Common Mistakes to Avoid:**")
                    for mistake in reference.common_mistakes:
                        st.markdown(f"  - {mistake}")

                if reference.variations:
                    st.markdown(f"**Variations:** {', '.join(reference.variations)}")
        else:
            # Exercise not in library
            st.info(f"**{exercise_name}** - No additional reference information available.")


def display_schedule_tab(workout_plan, profile) -> None:
    """Display the schedule to calendar tab."""
    st.subheader("📅 Schedule Workouts to Calendar")
    st.caption("Add all workouts to your Google Calendar with custom times")

    # Start date picker
    start_date = st.date_input(
        "Start Date",
        value=date.today() + timedelta(days=1),
        help="When to start the workout plan",
    )

    st.markdown("### ⏰ Preferred Workout Times")
    st.caption("Set your preferred time for each workout day")

    # Get unique days from first week
    preferred_times = {}
    first_week = workout_plan.weeks[0]

    # Create time inputs for each workout day
    cols = st.columns(min(len(first_week), 3))  # Max 3 columns

    for idx, session in enumerate(first_week):
        col_idx = idx % 3
        with cols[col_idx]:
            # Extract day name (e.g., "Day 1: Push" -> "Day 1")
            day_display = session.day_name.split(":")[0] if ":" in session.day_name else session.day_name

            time = st.time_input(
                day_display,
                value=None,  # No default, will use 7 AM
                key=f"time_{idx}",
                help=f"Preferred time for {session.focus}",
            )

            if time:
                preferred_times[day_display] = time.strftime("%H:%M")
            else:
                preferred_times[day_display] = "07:00"  # Default

    st.markdown("---")

    # Preview
    st.markdown("### 📋 Preview")

    if workout_plan:
        total_sessions = sum(len(week) for week in workout_plan.weeks)
        st.write(f"**Total Workouts:** {total_sessions} sessions over {len(workout_plan.weeks)} week(s)")

        # Show first few scheduled times
        preview_date = start_date
        st.write("**First few workouts:**")
        for i, session in enumerate(workout_plan.weeks[0][:3]):
            day_name = session.day_name.split(":")[0] if ":" in session.day_name else session.day_name
            time_str = preferred_times.get(day_name, "07:00")
            st.write(f"  - {preview_date.strftime('%A, %B %d')}: {session.focus} at {time_str}")
            preview_date += timedelta(days=1)

    st.markdown("---")

    # Schedule button
    if st.button("📅 Add All Workouts to Calendar", type="primary", use_container_width=True):
        # Flatten all weeks into single list of sessions
        all_sessions = []
        for week in workout_plan.weeks:
            all_sessions.extend(week)

        # Get user timezone from profile
        user_timezone = profile.get("timezone", "UTC") if profile else "UTC"

        with st.spinner(f"Scheduling {len(all_sessions)} workouts..."):
            success, message, events = schedule_workouts_bulk(
                workout_sessions=all_sessions,
                start_date=start_date,
                preferred_times=preferred_times,
                user_timezone=user_timezone,
            )

        if success:
            st.success(f"✅ {message}")
            st.session_state["scheduled_workouts"] = events

            # Show calendar links
            st.markdown("### ✅ Scheduled Workouts")
            for event in events[:5]:  # Show first 5
                time_display = event["time"].strftime("%B %d at %I:%M %p")
                if "html_link" in event and event["html_link"]:
                    st.markdown(f"- [{event['session']}]({event['html_link']}) - {time_display}")
                else:
                    st.markdown(f"- {event['session']} - {time_display}")

            if len(events) > 5:
                st.caption(f"...and {len(events) - 5} more workouts")
        else:
            st.error(f"❌ {message}")

            if "not configured" in message.lower():
                st.info(
                    "To enable calendar integration:\n"
                    "1. Set up Google Calendar credentials (see README.md)\n"
                    "2. Add `GOOGLE_CREDENTIALS_PATH` to your `.env` file\n"
                    "3. Complete the OAuth flow"
                )


def display_downloads_tab(workout_plan, profile) -> None:
    """Display the downloads/export tab."""
    st.subheader("⬇️ Export Your Workout Plan")
    st.markdown("Download your workout plan in various formats for easy reference.")

    exporter = WorkoutPlanExporter()

    # Workout plan exports
    st.markdown("### 📋 Workout Plan Exports")

    export_col1, export_col2, export_col3 = st.columns(3)

    with export_col1:
        json_data = exporter.to_json(workout_plan)
        st.download_button(
            "📄 Download JSON",
            data=json_data,
            file_name="workout_plan.json",
            mime="application/json",
            use_container_width=True,
            help="Full workout plan data in JSON format",
        )

    with export_col2:
        csv_data = exporter.to_csv(workout_plan)
        st.download_button(
            "📊 Download CSV",
            data=csv_data,
            file_name="exercises.csv",
            mime="text/csv",
            use_container_width=True,
            help="Exercise list in spreadsheet format",
        )

    with export_col3:
        md_data = exporter.to_markdown(workout_plan)
        st.download_button(
            "📝 Download Markdown",
            data=md_data,
            file_name="workout_plan.md",
            mime="text/markdown",
            use_container_width=True,
            help="Formatted workout plan for reading",
        )

    st.markdown("---")

    # Calendar export
    st.markdown("### 📅 Calendar Export")
    st.caption("Download as iCalendar file to import into any calendar app")

    # Get start date and timezone
    start_date = st.date_input(
        "Plan Start Date",
        value=date.today() + timedelta(days=1),
        key="ical_start_date",
    )

    user_timezone = profile.get("timezone", "UTC") if profile else "UTC"

    # Use default times for iCal export
    preferred_times = get_preferred_time_defaults()

    try:
        ical_data = exporter.to_icalendar(
            workout_plan,
            start_date=start_date,
            preferred_times=preferred_times,
            timezone=user_timezone,
        )

        st.download_button(
            "📅 Download iCalendar (.ics)",
            data=ical_data,
            file_name="workouts.ics",
            mime="text/calendar",
            use_container_width=True,
            help="Import this file into Google Calendar, Outlook, Apple Calendar, etc.",
        )

        st.info(
            "💡 **Tip:** Download the .ics file and import it into your calendar app. "
            "This creates all workout events at once without needing Google Calendar integration."
        )

    except ImportError:
        st.warning(
            "⚠️ iCalendar export requires the `icalendar` package. "
            "Install it with: `pip install icalendar`"
        )


# Run main function
main()
