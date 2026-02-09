"""Meal plan export functionality.

Exports meal plans to various formats: JSON, CSV, PDF, and calendar events.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any

from meal_planning.generator import MealPlan


class MealPlanExporter:
    """Export meal plans to various formats."""

    def to_json(self, meal_plan: MealPlan) -> str:
        """Export meal plan as JSON string.

        Args:
            meal_plan: The meal plan to export.

        Returns:
            JSON string representation.
        """
        return json.dumps(meal_plan.to_dict(), indent=2)

    def to_csv(self, meal_plan: MealPlan) -> str:
        """Export meal plan as CSV string.

        Args:
            meal_plan: The meal plan to export.

        Returns:
            CSV string with meal details.
        """
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Date",
            "Meal Type",
            "Name",
            "Description",
            "Calories",
            "Protein (g)",
            "Carbs (g)",
            "Fat (g)",
            "Prep Time (min)",
            "Ingredients",
        ])

        # Data rows
        for day in meal_plan.days:
            for meal_type, meal in [
                ("Breakfast", day.breakfast),
                ("Lunch", day.lunch),
                ("Dinner", day.dinner),
            ]:
                writer.writerow([
                    day.date,
                    meal_type,
                    meal.name,
                    meal.description,
                    meal.calories,
                    meal.protein_g,
                    meal.carbs_g,
                    meal.fat_g,
                    meal.prep_time_min,
                    "; ".join(meal.ingredients),
                ])

            # Add snacks
            for i, snack in enumerate(day.snacks, 1):
                writer.writerow([
                    day.date,
                    f"Snack {i}",
                    snack.name,
                    snack.description,
                    snack.calories,
                    snack.protein_g,
                    snack.carbs_g,
                    snack.fat_g,
                    snack.prep_time_min,
                    "; ".join(snack.ingredients),
                ])

        return output.getvalue()

    def to_markdown(self, meal_plan: MealPlan) -> str:
        """Export meal plan as Markdown string.

        Args:
            meal_plan: The meal plan to export.

        Returns:
            Markdown formatted meal plan.
        """
        lines = [
            f"# Meal Plan",
            "",
            f"**Dietary Preference:** {meal_plan.dietary_preference}",
            f"**Daily Calorie Target:** {meal_plan.calorie_target} kcal",
            f"**Restrictions:** {', '.join(meal_plan.restrictions) if meal_plan.restrictions else 'None'}",
            "",
            "---",
            "",
        ]

        for day in meal_plan.days:
            date_obj = datetime.fromisoformat(day.date)
            day_name = date_obj.strftime("%A, %B %d, %Y")

            lines.extend([
                f"## {day_name}",
                "",
                f"**Daily Totals:** {day.total_calories} kcal | {day.total_protein:.1f}g protein",
                "",
            ])

            # Breakfast
            lines.extend(self._format_meal_markdown("Breakfast", day.breakfast))

            # Lunch
            lines.extend(self._format_meal_markdown("Lunch", day.lunch))

            # Dinner
            lines.extend(self._format_meal_markdown("Dinner", day.dinner))

            # Snacks
            if day.snacks:
                lines.append("### Snacks")
                lines.append("")
                for snack in day.snacks:
                    lines.extend([
                        f"**{snack.name}** ({snack.calories} kcal)",
                        "",
                        snack.description,
                        "",
                    ])

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _format_meal_markdown(self, meal_type: str, meal: Any) -> list[str]:
        """Format a single meal as Markdown.

        Args:
            meal_type: Breakfast, Lunch, or Dinner.
            meal: Meal object.

        Returns:
            List of Markdown lines.
        """
        return [
            f"### {meal_type}: {meal.name}",
            "",
            meal.description,
            "",
            f"**Nutrition:** {meal.calories} kcal | "
            f"P: {meal.protein_g}g | C: {meal.carbs_g}g | F: {meal.fat_g}g",
            "",
            f"**Prep Time:** {meal.prep_time_min} minutes",
            "",
            "**Ingredients:**",
            *[f"- {ingredient}" for ingredient in meal.ingredients],
            "",
        ]

    def save_to_file(self, meal_plan: MealPlan, file_path: str | Path, format: str = "json") -> None:
        """Save meal plan to file.

        Args:
            meal_plan: The meal plan to save.
            file_path: Path to save the file.
            format: Export format (json, csv, or markdown).
        """
        path = Path(file_path)

        if format == "json":
            content = self.to_json(meal_plan)
        elif format == "csv":
            content = self.to_csv(meal_plan)
        elif format == "markdown":
            content = self.to_markdown(meal_plan)
        else:
            raise ValueError(f"Unsupported format: {format}")

        path.write_text(content, encoding="utf-8")

    def to_calendar_events(self, meal_plan: MealPlan) -> list[dict[str, Any]]:
        """Convert meal plan to calendar event format.

        Args:
            meal_plan: The meal plan to convert.

        Returns:
            List of calendar event dicts suitable for Google Calendar API.
        """
        events = []

        for day in meal_plan.days:
            date_obj = datetime.fromisoformat(day.date)

            # Breakfast - 8:00 AM
            events.append({
                "title": f"🍳 Breakfast: {day.breakfast.name}",
                "start_time": date_obj.replace(hour=8, minute=0).isoformat(),
                "duration_minutes": day.breakfast.prep_time_min + 20,  # Prep + eating
                "description": f"{day.breakfast.description}\n\n"
                              f"Calories: {day.breakfast.calories} kcal\n"
                              f"Ingredients: {', '.join(day.breakfast.ingredients)}",
            })

            # Lunch - 12:30 PM
            events.append({
                "title": f"🥗 Lunch: {day.lunch.name}",
                "start_time": date_obj.replace(hour=12, minute=30).isoformat(),
                "duration_minutes": day.lunch.prep_time_min + 30,
                "description": f"{day.lunch.description}\n\n"
                              f"Calories: {day.lunch.calories} kcal\n"
                              f"Ingredients: {', '.join(day.lunch.ingredients)}",
            })

            # Dinner - 6:30 PM
            events.append({
                "title": f"🍽️ Dinner: {day.dinner.name}",
                "start_time": date_obj.replace(hour=18, minute=30).isoformat(),
                "duration_minutes": day.dinner.prep_time_min + 40,
                "description": f"{day.dinner.description}\n\n"
                              f"Calories: {day.dinner.calories} kcal\n"
                              f"Ingredients: {', '.join(day.dinner.ingredients)}",
            })

        return events
