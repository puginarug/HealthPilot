"""Nutrition agent tools.

Tools for meal planning and nutrition tracking (non-RAG).
Web search tools are now in web_search_tools.py.
"""

from __future__ import annotations

import json
import logging
from datetime import date

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def generate_meal_plan(
    num_days: int,
    dietary_preference: str,
    calorie_target: int,
    restrictions: str = "",
) -> str:
    """Generate a personalized meal plan with nutritional information.

    Creates a structured multi-day meal plan with breakfast, lunch, dinner, and snacks.
    Each meal includes detailed nutrition info, ingredients, and prep time.

    Args:
        num_days: Number of days to plan (1-7).
        dietary_preference: Diet type (omnivore, vegetarian, vegan, pescatarian).
        calorie_target: Daily calorie target (e.g., 2000).
        restrictions: Comma-separated list of allergies/restrictions (e.g., "nuts, dairy").

    Returns:
        Formatted meal plan with daily totals and meal details.
    """
    try:
        from meal_planning.generator import MealPlanGenerator

        # Validate inputs
        if not 1 <= num_days <= 7:
            return "Error: num_days must be between 1 and 7"
        if calorie_target < 1000 or calorie_target > 5000:
            return "Error: calorie_target must be between 1000 and 5000"

        valid_prefs = ["omnivore", "vegetarian", "vegan", "pescatarian"]
        if dietary_preference.lower() not in valid_prefs:
            return f"Error: dietary_preference must be one of {valid_prefs}"

        # Parse restrictions
        restriction_list = [r.strip() for r in restrictions.split(",") if r.strip()] if restrictions else []

        # Generate meal plan
        generator = MealPlanGenerator()
        meal_plan = generator.generate(
            num_days=num_days,
            dietary_preference=dietary_preference.lower(),
            calorie_target=calorie_target,
            restrictions=restriction_list,
        )

        # Format output
        lines = [
            f"Generated {num_days}-day {dietary_preference} meal plan ({calorie_target} kcal/day)",
            "",
        ]

        for day in meal_plan.days:
            date_str = date.fromisoformat(day.date).strftime("%A, %b %d")
            lines.append(f"=== {date_str} ===")
            lines.append(f"Daily totals: {day.total_calories} kcal | {day.total_protein:.1f}g protein")
            lines.append("")

            for meal_type, meal in [
                ("Breakfast", day.breakfast),
                ("Lunch", day.lunch),
                ("Dinner", day.dinner),
            ]:
                lines.append(f"{meal_type}: {meal.name} ({meal.calories} kcal)")
                lines.append(f"  {meal.description}")
                lines.append(f"  Macros: P:{meal.protein_g}g C:{meal.carbs_g}g F:{meal.fat_g}g")
                lines.append(f"  Prep: {meal.prep_time_min} min")
                lines.append("")

            if day.snacks:
                lines.append(f"Snacks: {', '.join(s.name for s in day.snacks)}")
                lines.append("")

        logger.info("Generated %d-day meal plan (%s, %d kcal)", num_days, dietary_preference, calorie_target)
        return "\n".join(lines)

    except Exception as e:
        logger.error("Meal plan generation failed: %s", e)
        return f"Error generating meal plan: {e}"


@tool
def export_meal_plan_json(meal_plan_json: str, file_path: str = "meal_plan.json") -> str:
    """Export a meal plan to JSON file.

    Args:
        meal_plan_json: JSON string of the meal plan (from generate_meal_plan).
        file_path: Output file path (default: meal_plan.json).

    Returns:
        Success message with file path.
    """
    try:
        from pathlib import Path

        # Validate JSON
        json.loads(meal_plan_json)

        # Save to file
        output_path = Path(file_path)
        output_path.write_text(meal_plan_json, encoding="utf-8")

        logger.info("Exported meal plan to: %s", output_path)
        return f"Meal plan saved to {output_path.absolute()}"

    except json.JSONDecodeError:
        return "Error: Invalid meal plan JSON format"
    except Exception as e:
        logger.error("Meal plan export failed: %s", e)
        return f"Error exporting meal plan: {e}"
