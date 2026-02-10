"""HealthPilot Streamlit application entry point.

Run with: uv run streamlit run streamlit_app.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import streamlit as st

from config import get_settings, setup_logging, setup_langsmith

setup_logging()
setup_langsmith()
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="HealthPilot",
    page_icon=":material/health_and_safety:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar: user profile summary
with st.sidebar:
    st.title("HealthPilot")
    st.caption("AI-Powered Health Assistant")
    st.divider()

    settings = get_settings()
    profile_path = settings.user_profile_path
    if profile_path.exists():
        with open(profile_path) as f:
            profile = json.load(f)
        st.subheader("User Profile")
        st.write(f"**Name:** {profile.get('name', 'N/A')}")
        st.write(f"**Fitness Level:** {profile.get('fitness_level', 'N/A')}")
        st.write(f"**Daily Step Goal:** {profile.get('daily_step_goal', 'N/A'):,}")
        st.write(f"**Calorie Target:** {profile.get('daily_calorie_target', 'N/A'):,} kcal")
        st.write(f"**Sleep Goal:** {profile.get('sleep_goal_hours', 'N/A')}h")
    else:
        st.info("No user profile found. Create `data/user_profile.json` to personalize.")

    st.divider()

    # API key status
    st.subheader("Status")
    has_anthropic = settings.has_anthropic_key()
    has_openai = settings.has_openai_key()
    has_langsmith = settings.has_langsmith()

    st.write(f"Claude API: {'Connected' if has_anthropic else 'Not configured'}")
    st.write(f"Embeddings: {'Connected' if has_openai else 'Not configured'}")
    st.write(f"LangSmith: {'Active' if has_langsmith else 'Inactive'}")

# Define pages (6-page structure)
profile_page = st.Page("pages/0_Profile.py", title="Profile", icon=":material/person:")
chat_page = st.Page("pages/1_Chat.py", title="Chat", icon=":material/chat:")
dashboard_page = st.Page("pages/2_Dashboard.py", title="Dashboard", icon=":material/monitoring:")
meal_plan_page = st.Page("pages/3_Meal_Plan.py", title="Meal Planner", icon=":material/restaurant:")
workout_page = st.Page("pages/4_Workout_Plan.py", title="Workout Planner", icon=":material/fitness_center:")
data_page = st.Page("pages/5_Data_Management.py", title="Data Upload", icon=":material/upload:")

nav = st.navigation({
    "Settings": [profile_page, data_page],
    "AI Assistant": [chat_page],
    "Planning": [meal_plan_page, workout_page],
    "Analytics": [dashboard_page],
})

nav.run()
