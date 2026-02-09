"""Meal Planning page.

Interactive meal plan generation using the nutrition agent with LLM-powered suggestions.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

import streamlit as st

from analytics.nutrition_calculator import (
    ActivityLevel,
    Goal,
    NutritionCalculator,
    Sex,
)
from config import get_settings
from meal_planning.exporter import MealPlanExporter
from meal_planning.generator import MealPlanGenerator
from meal_planning.shopping_list import generate_shopping_list

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Meal Planner", page_icon="🍽️", layout="wide")

settings = get_settings()


def main() -> None:
    """Render the meal planning page."""
    st.header("🍽️ Meal Planner")

    # Check API key
    if not settings.has_llm_key():
        st.error(
            f"No {settings.llm_provider.upper()} API key found. "
            f"Add your API key to `.env` to use meal planning."
        )
        return

    st.markdown(
        """
        Generate personalized meal plans powered by AI and backed by USDA nutritional data.
        Includes nutrition info, ingredients, prep times, and an organized shopping list.
        """
    )

    # Load user profile for recommendations
    profile_path = Path("data/user_profile.json")
    recommendations = None

    if profile_path.exists():
        try:
            with open(profile_path) as f:
                profile = json.load(f)

            # Calculate recommendations if we have the required data
            if all(key in profile for key in ["weight_kg", "height_cm", "age", "sex"]):
                activity_level = ActivityLevel(profile.get("activity_level", "moderately_active"))
                sex = Sex(profile["sex"])

                recommendations = NutritionCalculator.get_recommendations(
                    weight_kg=profile["weight_kg"],
                    height_cm=profile["height_cm"],
                    age=profile["age"],
                    sex=sex,
                    activity_level=activity_level,
                    goal=Goal.MAINTENANCE,
                )
        except Exception as e:
            logger.error("Failed to load user profile: %s", e)

    # Show recommendations at the top
    if recommendations:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.metric(
                "📊 Recommended Daily Calories",
                f"{recommendations.target_calories} kcal",
                help=f"Based on BMR: {recommendations.bmr} kcal, TDEE: {recommendations.tdee} kcal"
            )
        with col2:
            st.metric(
                "💪 Protein Target",
                f"{recommendations.protein_recommended_g:.0f}g",
                help=f"Range: {recommendations.protein_min_g:.0f}-{recommendations.protein_max_g:.0f}g"
            )
        with col3:
            use_custom = st.toggle("Custom Values", value=False, help="Override recommended values")

        default_calories = recommendations.target_calories
    else:
        default_calories = 2400
        use_custom = True

    st.markdown("---")

    # Main configuration in columns
    st.subheader("⚙️ Meal Plan Settings")

    col1, col2 = st.columns(2)

    with col1:
        dietary_preference = st.selectbox(
            "Dietary Preference",
            ["Omnivore", "Vegetarian", "Vegan", "Pescatarian"],
            help="Choose your dietary style",
        )

        if use_custom:
            calorie_target = st.number_input(
                "Daily Calorie Target",
                min_value=1000,
                max_value=5000,
                value=default_calories,
                step=100,
                help="Total calories per day",
            )
        else:
            calorie_target = default_calories
            st.info(f"Using recommended: **{calorie_target} kcal/day**")

    with col2:
        num_days = st.slider(
            "Number of Days",
            min_value=1,
            max_value=7,
            value=5,
            help="How many days to plan",
        )

        restrictions = st.multiselect(
            "Allergies / Restrictions",
            ["Dairy", "Eggs", "Nuts", "Soy", "Shellfish", "Gluten", "Fish"],
            help="Select any foods to avoid",
        )

    st.markdown("---")

    # Generation button
    generate_button = st.button(
        "🔄 Generate Meal Plan",
        type="primary",
        use_container_width=True,
    )

    # Generate meal plan
    if generate_button:
        with st.spinner("Generating your personalized meal plan..."):
            try:
                generator = MealPlanGenerator()
                meal_plan = generator.generate(
                    num_days=num_days,
                    dietary_preference=dietary_preference.lower(),
                    calorie_target=calorie_target,
                    restrictions=restrictions,
                    start_date=date.today(),
                )

                # Store in session state
                st.session_state["meal_plan"] = meal_plan
                st.success(f"✅ Generated {num_days}-day meal plan!")

            except Exception as e:
                logger.error("Meal plan generation failed: %s", e)
                st.error(f"Error generating meal plan: {e}")
                return

    # Display meal plan if available
    if "meal_plan" not in st.session_state:
        st.markdown("---")
        st.info("### 👆 Click 'Generate Meal Plan' to get started!")
        return

    meal_plan = st.session_state["meal_plan"]

    st.markdown("---")

    # Main tabs for Meal Plan, Shopping List, and Downloads
    tab1, tab2, tab3 = st.tabs(["📋 Meal Plan", "🛒 Shopping List", "⬇️ Downloads"])

    # ===== TAB 1: MEAL PLAN =====
    with tab1:
        st.subheader(f"📅 Your {len(meal_plan.days)}-Day Meal Plan")

        st.info(
            f"**Dietary Preference:** {meal_plan.dietary_preference.capitalize()} | "
            f"**Target:** {meal_plan.calorie_target} kcal/day | "
            f"**Restrictions:** {', '.join(meal_plan.restrictions) if meal_plan.restrictions else 'None'}"
        )

        # Tabs for each day
        day_tabs = st.tabs([f"Day {i+1}" for i in range(len(meal_plan.days))])

        for i, (day_tab, day) in enumerate(zip(day_tabs, meal_plan.days)):
            with day_tab:
                # Day summary
                date_obj = date.fromisoformat(day.date)
                day_name = date_obj.strftime("%A, %B %d, %Y")

                st.markdown(f"### {day_name}")

                # Daily totals
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Calories", f"{day.total_calories} kcal")
                col2.metric("Protein", f"{day.total_protein:.1f}g")
                col3.metric("Meals", f"{3 + len(day.snacks)}")

                st.markdown("---")

                # Breakfast
                display_meal("🍳 Breakfast", day.breakfast)

                # Lunch
                display_meal("🥗 Lunch", day.lunch)

                # Dinner
                display_meal("🍽️ Dinner", day.dinner)

                # Snacks
                if day.snacks:
                    st.markdown("### 🍿 Snacks")
                    cols = st.columns(len(day.snacks))
                    for col, snack in zip(cols, day.snacks):
                        with col:
                            with st.expander(f"{snack.name}"):
                                st.markdown(f"**{snack.description}**")
                                st.markdown(f"📊 {snack.calories} kcal")
                                st.markdown(
                                    f"**Macros:** P:{snack.protein_g}g | "
                                    f"C:{snack.carbs_g}g | F:{snack.fat_g}g"
                                )

    # ===== TAB 2: SHOPPING LIST =====
    with tab2:
        st.subheader("🛒 Shopping List")
        st.caption(f"Organized grocery list for your {len(meal_plan.days)}-day meal plan")

        # Generate shopping list
        with st.spinner("Generating shopping list..."):
            shopping_list = generate_shopping_list(meal_plan)

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Items", shopping_list.total_items)
        col2.metric("Categories", len(shopping_list.items_by_category))
        col3.metric("Days Covered", shopping_list.meal_plan_days)

        st.markdown("---")

        # Display items by category
        for category, items in shopping_list.items_by_category.items():
            with st.expander(f"**{category}** ({len(items)} items)", expanded=True):
                for item in items:
                    # Format quantity nicely
                    qty_str = f"{item.quantity:.1f}" if item.quantity % 1 else f"{int(item.quantity)}"

                    st.markdown(f"✓ **{qty_str} {item.unit}** {item.name}")
                    st.caption(f"Used in: {', '.join(item.meal_sources[:3])}{'...' if len(item.meal_sources) > 3 else ''}")

    # ===== TAB 3: DOWNLOADS =====
    with tab3:
        st.subheader("⬇️ Export Your Meal Plan")
        st.markdown("Download your meal plan in different formats for easy reference.")

        exporter = MealPlanExporter()

        # Meal plan exports
        st.markdown("### 📋 Meal Plan Exports")

        export_col1, export_col2, export_col3 = st.columns(3)

        with export_col1:
            json_data = exporter.to_json(meal_plan)
            st.download_button(
                "📄 Download JSON",
                data=json_data,
                file_name="meal_plan.json",
                mime="application/json",
                use_container_width=True,
            )

        with export_col2:
            csv_data = exporter.to_csv(meal_plan)
            st.download_button(
                "📊 Download CSV",
                data=csv_data,
                file_name="meal_plan.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with export_col3:
            md_data = exporter.to_markdown(meal_plan)
            st.download_button(
                "📝 Download Markdown",
                data=md_data,
                file_name="meal_plan.md",
                mime="text/markdown",
                use_container_width=True,
            )

        st.markdown("---")

        # Shopping list export
        st.markdown("### 🛒 Shopping List Export")

        shopping_list = generate_shopping_list(meal_plan)

        # Generate shopping list as markdown text
        shopping_md_lines = [
            f"# Shopping List",
            f"",
            f"Generated: {shopping_list.generated_date}",
            f"Meal Plan: {shopping_list.meal_plan_days} days ({shopping_list.dietary_preference})",
            f"Total Items: {shopping_list.total_items}",
            f"",
        ]

        for category, items in shopping_list.items_by_category.items():
            shopping_md_lines.append(f"## {category}")
            shopping_md_lines.append("")
            for item in items:
                qty_str = f"{item.quantity:.1f}" if item.quantity % 1 else f"{int(item.quantity)}"
                shopping_md_lines.append(f"- [ ] {qty_str} {item.unit} {item.name}")
            shopping_md_lines.append("")

        shopping_md = "\n".join(shopping_md_lines)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                "📝 Shopping List (Markdown)",
                data=shopping_md,
                file_name="shopping_list.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with col2:
            st.download_button(
                "📄 Shopping List (Text)",
                data=shopping_md,
                file_name="shopping_list.txt",
                mime="text/plain",
                use_container_width=True,
            )


def display_meal(title: str, meal: any) -> None:
    """Display a single meal with details.

    Args:
        title: Meal title (e.g., "Breakfast").
        meal: Meal object with all details.
    """
    st.markdown(f"### {title}: {meal.name}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**Description:** {meal.description}")

        st.markdown("**Ingredients:**")
        for ingredient in meal.ingredients:
            st.markdown(f"- {ingredient}")

    with col2:
        st.markdown("**Nutrition Info:**")
        st.markdown(f"🔥 Calories: **{meal.calories} kcal**")
        st.markdown(f"💪 Protein: **{meal.protein_g}g**")
        st.markdown(f"🍞 Carbs: **{meal.carbs_g}g**")
        st.markdown(f"🥑 Fat: **{meal.fat_g}g**")
        st.markdown(f"⏱️ Prep Time: **{meal.prep_time_min} min**")

    st.markdown("---")


# Run main function
main()
