"""User Profile page.

Interactive form for creating and editing user profile data.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import streamlit as st

from config import get_settings

logger = logging.getLogger(__name__)

st.set_page_config(page_title="User Profile", page_icon="👤", layout="wide")

settings = get_settings()


def main() -> None:
    """Render the user profile page."""
    st.header("👤 User Profile")
    st.caption("Manage your personal health data and preferences")

    profile_path = Path("data/user_profile.json")

    # Load existing profile if it exists
    existing_profile = {}
    if profile_path.exists():
        try:
            with open(profile_path) as f:
                existing_profile = json.load(f)
        except Exception as e:
            logger.error("Failed to load profile: %s", e)
            st.error(f"Error loading profile: {e}")

    # Create tabs for different profile sections
    tab1, tab2, tab3 = st.tabs(["📋 Basic Info", "🏃 Fitness & Activity", "⚙️ Preferences"])

    # ===== TAB 1: BASIC INFO =====
    with tab1:
        st.subheader("Basic Information")

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Name",
                value=existing_profile.get("name", ""),
                help="Your full name",
            )

            age = st.number_input(
                "Age",
                min_value=10,
                max_value=120,
                value=existing_profile.get("age", 30),
                help="Your age in years",
            )

            sex = st.selectbox(
                "Sex",
                ["male", "female"],
                index=0 if existing_profile.get("sex", "male") == "male" else 1,
                help="Biological sex (affects BMR calculations)",
            )

        with col2:
            height_cm = st.number_input(
                "Height (cm)",
                min_value=100,
                max_value=250,
                value=existing_profile.get("height_cm", 170),
                help="Your height in centimeters",
            )

            weight_kg = st.number_input(
                "Weight (kg)",
                min_value=30.0,
                max_value=300.0,
                value=float(existing_profile.get("weight_kg", 70.0)),
                step=0.1,
                help="Your current weight in kilograms",
            )

            timezone = st.selectbox(
                "Timezone",
                [
                    "UTC",
                    "America/New_York",
                    "America/Chicago",
                    "America/Denver",
                    "America/Los_Angeles",
                    "Europe/London",
                    "Europe/Paris",
                    "Europe/Berlin",
                    "Asia/Jerusalem",
                    "Asia/Tokyo",
                    "Asia/Shanghai",
                    "Australia/Sydney",
                ],
                index=0 if existing_profile.get("timezone", "UTC") == "UTC" else
                      ["UTC", "America/New_York", "America/Chicago", "America/Denver",
                       "America/Los_Angeles", "Europe/London", "Europe/Paris", "Europe/Berlin",
                       "Asia/Jerusalem", "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney"].index(
                           existing_profile.get("timezone", "UTC")
                       ) if existing_profile.get("timezone", "UTC") in [
                           "UTC", "America/New_York", "America/Chicago", "America/Denver",
                           "America/Los_Angeles", "Europe/London", "Europe/Paris", "Europe/Berlin",
                           "Asia/Jerusalem", "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney"
                       ] else 0,
                help="Your timezone for calendar integration",
            )

    # ===== TAB 2: FITNESS & ACTIVITY =====
    with tab2:
        st.subheader("Fitness & Activity")

        col1, col2 = st.columns(2)

        with col1:
            fitness_level = st.selectbox(
                "Fitness Level",
                ["beginner", "intermediate", "advanced"],
                index=["beginner", "intermediate", "advanced"].index(
                    existing_profile.get("fitness_level", "intermediate")
                ),
                help="Your current training experience",
            )

            activity_level = st.selectbox(
                "Activity Level",
                ["sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"],
                index=["sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"].index(
                    existing_profile.get("activity_level", "moderately_active")
                ),
                help="Your daily activity level (affects calorie calculations)",
            )

            daily_step_goal = st.number_input(
                "Daily Step Goal",
                min_value=1000,
                max_value=50000,
                value=existing_profile.get("daily_step_goal", 10000),
                step=1000,
                help="Target number of steps per day",
            )

        with col2:
            # Fitness goals
            st.markdown("**Fitness Goals** (select multiple)")

            goal_options = {
                "strength": st.checkbox(
                    "Strength",
                    value="strength" in existing_profile.get("fitness_goals", []),
                ),
                "hypertrophy": st.checkbox(
                    "Muscle Growth (Hypertrophy)",
                    value="hypertrophy" in existing_profile.get("fitness_goals", []) or
                          "build lean muscle" in existing_profile.get("fitness_goals", []),
                ),
                "endurance": st.checkbox(
                    "Endurance",
                    value="endurance" in existing_profile.get("fitness_goals", []) or
                          "improve cardiovascular fitness" in existing_profile.get("fitness_goals", []),
                ),
                "weight_loss": st.checkbox(
                    "Weight Loss",
                    value="weight_loss" in existing_profile.get("fitness_goals", []),
                ),
                "flexibility": st.checkbox(
                    "Flexibility",
                    value="flexibility" in existing_profile.get("fitness_goals", []),
                ),
            }

            fitness_goals = [goal for goal, checked in goal_options.items() if checked]

            # Equipment available
            st.markdown("**Available Equipment** (select multiple)")

            equipment_options = {
                "bodyweight": st.checkbox(
                    "Bodyweight",
                    value="bodyweight" in existing_profile.get("available_equipment", []),
                ),
                "dumbbells": st.checkbox(
                    "Dumbbells",
                    value="dumbbells" in existing_profile.get("available_equipment", []),
                ),
                "barbell": st.checkbox(
                    "Barbell",
                    value="barbell" in existing_profile.get("available_equipment", []),
                ),
                "pull-up bar": st.checkbox(
                    "Pull-up Bar",
                    value="pull-up bar" in existing_profile.get("available_equipment", []),
                ),
                "yoga mat": st.checkbox(
                    "Yoga Mat",
                    value="yoga mat" in existing_profile.get("available_equipment", []) or
                          "yoga_mat" in existing_profile.get("available_equipment", []),
                ),
                "running shoes": st.checkbox(
                    "Running Shoes",
                    value="running shoes" in existing_profile.get("available_equipment", []) or
                          "running_shoes" in existing_profile.get("available_equipment", []),
                ),
            }

            available_equipment = [equip for equip, checked in equipment_options.items() if checked]

    # ===== TAB 3: PREFERENCES =====
    with tab3:
        st.subheader("Health & Nutrition Preferences")

        col1, col2 = st.columns(2)

        with col1:
            daily_calorie_target = st.number_input(
                "Daily Calorie Target (kcal)",
                min_value=1000,
                max_value=5000,
                value=existing_profile.get("daily_calorie_target", 2400),
                step=100,
                help="Target daily calorie intake",
            )

            sleep_goal_hours = st.number_input(
                "Sleep Goal (hours)",
                min_value=4.0,
                max_value=12.0,
                value=float(existing_profile.get("sleep_goal_hours", 8.0)),
                step=0.5,
                help="Target hours of sleep per night",
            )

        with col2:
            # Dietary restrictions
            st.markdown("**Dietary Restrictions** (select multiple)")

            restriction_options = {
                "vegetarian": st.checkbox(
                    "Vegetarian",
                    value="vegetarian" in existing_profile.get("dietary_restrictions", []),
                ),
                "vegan": st.checkbox(
                    "Vegan",
                    value="vegan" in existing_profile.get("dietary_restrictions", []),
                ),
                "gluten-free": st.checkbox(
                    "Gluten-Free",
                    value="gluten-free" in existing_profile.get("dietary_restrictions", []),
                ),
                "dairy-free": st.checkbox(
                    "Dairy-Free",
                    value="dairy-free" in existing_profile.get("dietary_restrictions", []),
                ),
                "nut-free": st.checkbox(
                    "Nut-Free",
                    value="nut-free" in existing_profile.get("dietary_restrictions", []),
                ),
            }

            dietary_restrictions = [rest for rest, checked in restriction_options.items() if checked]

            preferred_exercise_times = st.multiselect(
                "Preferred Exercise Times",
                ["morning", "afternoon", "evening"],
                default=existing_profile.get("preferred_exercise_times", ["morning"]),
                help="When do you prefer to work out?",
            )

    # Save button
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col2:
        if st.button("💾 Save Profile", type="primary", use_container_width=True):
            # Build profile dictionary
            profile = {
                # Basic info
                "name": name,
                "age": age,
                "sex": sex,
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "timezone": timezone,

                # Fitness & activity
                "fitness_level": fitness_level,
                "activity_level": activity_level,
                "daily_step_goal": daily_step_goal,
                "fitness_goals": fitness_goals,
                "available_equipment": available_equipment,

                # Preferences
                "daily_calorie_target": daily_calorie_target,
                "sleep_goal_hours": sleep_goal_hours,
                "dietary_restrictions": dietary_restrictions,
                "preferred_exercise_times": preferred_exercise_times,
            }

            # Save to file
            try:
                # Ensure data directory exists
                profile_path.parent.mkdir(parents=True, exist_ok=True)

                with open(profile_path, "w") as f:
                    json.dump(profile, f, indent=2)

                st.success("✅ Profile saved successfully!")
                logger.info("Profile saved for user: %s", name)

            except Exception as e:
                logger.error("Failed to save profile: %s", e)
                st.error(f"Error saving profile: {e}")

    with col3:
        if profile_path.exists():
            if st.button("🗑️ Delete Profile", use_container_width=True):
                try:
                    profile_path.unlink()
                    st.success("Profile deleted successfully!")
                    st.rerun()
                except Exception as e:
                    logger.error("Failed to delete profile: %s", e)
                    st.error(f"Error deleting profile: {e}")

    # Show current profile as JSON (for reference)
    if existing_profile:
        with st.expander("📄 View Profile JSON", expanded=False):
            st.json(existing_profile)


# Run main function
main()
