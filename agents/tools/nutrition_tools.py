"""Nutrition agent tools.

Tools for searching nutritional data, accessing research, and meal planning.
"""

from __future__ import annotations

import json
import logging
from datetime import date

from langchain_core.tools import tool

from config import get_settings
from rag.retriever import HealthRetriever

logger = logging.getLogger(__name__)


@tool
def search_nutrition_knowledge(query: str, top_k: int = 5) -> str:
    """Search the USDA and PubMed nutrition knowledge base.

    Use this tool to find:
    - Nutritional information about specific foods
    - Evidence-based dietary guidance from research
    - Health benefits of nutrients or diets

    Args:
        query: A nutrition-related question or food item (e.g., "high protein foods",
               "Mediterranean diet benefits", "vitamin D sources").
        top_k: Number of results to return (default 5).

    Returns:
        Relevant nutrition information with source citations (USDA FDC IDs, PubMed PMIDs).
    """
    try:
        retriever = HealthRetriever(top_k=top_k)
        docs = retriever.retrieve(
            query,
            collections=["nutrition_docs", "pubmed_abstracts"],
            top_k=top_k,
        )

        if not docs:
            return (
                f"No results found for '{query}'. The knowledge base may not be populated yet. "
                f"Run `python -m rag.ingest --source all` to load nutrition data."
            )

        context = retriever.format_context(docs, max_length=3000)
        logger.info("Retrieved %d nutrition sources for query: %s", len(docs), query[:50])
        return context

    except Exception as e:
        logger.error("Nutrition search failed: %s", e)
        return f"Error searching nutrition knowledge base: {e}"


@tool
def lookup_food_nutrients(food_name: str) -> str:
    """Look up detailed nutrient information for a specific food.

    Args:
        food_name: Name of the food (e.g., "chicken breast", "brown rice", "avocado").

    Returns:
        Detailed nutrient breakdown per 100g including calories, protein, fat,
        carbs, vitamins, and minerals from USDA FoodData Central.
    """
    try:
        retriever = HealthRetriever(top_k=3)
        docs = retriever.retrieve(
            food_name,
            collections=["nutrition_docs"],  # USDA only
            top_k=3,
        )

        if not docs:
            return (
                f"Food '{food_name}' not found in database. Try a more general name or "
                f"ensure the USDA data is loaded (python -m rag.ingest --source usda)."
            )

        context = retriever.format_context(docs, max_length=2000)
        logger.info("Looked up nutrients for: %s", food_name)
        return context

    except Exception as e:
        logger.error("Food lookup failed: %s", e)
        return f"Error looking up food: {e}"


@tool
def search_dietary_research(topic: str, top_k: int = 3) -> str:
    """Search PubMed research abstracts on nutrition topics.

    Use this for evidence-based guidance on:
    - Dietary patterns (e.g., ketogenic, Mediterranean)
    - Nutrient effects and mechanisms
    - Diet-disease relationships

    Args:
        topic: Research topic (e.g., "omega-3 cardiovascular health",
               "fiber gut microbiome").
        top_k: Number of abstracts to return (default 3).

    Returns:
        PubMed abstracts with PMIDs and publication details.
    """
    try:
        retriever = HealthRetriever(top_k=top_k)
        docs = retriever.retrieve(
            topic,
            collections=["pubmed_abstracts"],  # PubMed only
            top_k=top_k,
        )

        if not docs:
            return (
                f"No research found on '{topic}'. Run `python -m rag.ingest --source pubmed` "
                f"to load PubMed abstracts."
            )

        context = retriever.format_context(docs, max_length=3000)
        logger.info("Retrieved %d research abstracts for: %s", len(docs), topic[:50])
        return context

    except Exception as e:
        logger.error("Research search failed: %s", e)
        return f"Error searching research: {e}"


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
