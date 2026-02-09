"""Meal plan generator using the nutrition agent.

Generates structured meal plans based on user preferences and goals.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from llm_factory import create_chat_llm

logger = logging.getLogger(__name__)


@dataclass
class Meal:
    """Single meal specification."""

    name: str
    description: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    prep_time_min: int
    ingredients: list[str]


@dataclass
class DayPlan:
    """Meal plan for one day."""

    date: str
    breakfast: Meal
    lunch: Meal
    dinner: Meal
    snacks: list[Meal]

    @property
    def total_calories(self) -> int:
        """Calculate total daily calories."""
        return (
            self.breakfast.calories
            + self.lunch.calories
            + self.dinner.calories
            + sum(s.calories for s in self.snacks)
        )

    @property
    def total_protein(self) -> float:
        """Calculate total daily protein."""
        return (
            self.breakfast.protein_g
            + self.lunch.protein_g
            + self.dinner.protein_g
            + sum(s.protein_g for s in self.snacks)
        )


@dataclass
class MealPlan:
    """Complete multi-day meal plan."""

    days: list[DayPlan]
    dietary_preference: str
    calorie_target: int
    restrictions: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "dietary_preference": self.dietary_preference,
            "calorie_target": self.calorie_target,
            "restrictions": self.restrictions,
            "days": [
                {
                    "date": day.date,
                    "breakfast": asdict(day.breakfast),
                    "lunch": asdict(day.lunch),
                    "dinner": asdict(day.dinner),
                    "snacks": [asdict(s) for s in day.snacks],
                    "totals": {
                        "calories": day.total_calories,
                        "protein_g": day.total_protein,
                    },
                }
                for day in self.days
            ],
        }


class MealPlanGenerator:
    """Generate structured meal plans using LLM with nutritional data."""

    def __init__(self) -> None:
        """Initialize the meal plan generator."""
        self.llm = create_chat_llm(temperature=0.7)  # More creative for meal variety

    def generate(
        self,
        num_days: int,
        dietary_preference: str,
        calorie_target: int,
        restrictions: list[str],
        start_date: date | None = None,
    ) -> MealPlan:
        """Generate a structured meal plan.

        Args:
            num_days: Number of days to plan (1-7).
            dietary_preference: omnivore, vegetarian, vegan, pescatarian.
            calorie_target: Daily calorie target.
            restrictions: List of allergies/restrictions.

        Returns:
            MealPlan object with complete daily meal specifications.
        """
        start = start_date or date.today()

        system_prompt = """You are a nutrition expert creating personalized meal plans.

Generate a detailed meal plan in valid JSON format with this exact structure:

{
  "days": [
    {
      "breakfast": {
        "name": "Meal Name",
        "description": "Brief description",
        "calories": 450,
        "protein_g": 25.0,
        "carbs_g": 45.0,
        "fat_g": 15.0,
        "prep_time_min": 15,
        "ingredients": ["ingredient1", "ingredient2"]
      },
      "lunch": { ... same structure ... },
      "dinner": { ... same structure ... },
      "snacks": [
        { ... same structure ... }
      ]
    }
  ]
}

Guidelines:
- Each meal should be realistic and practical
- Use common ingredients
- Balance macronutrients
- Include variety across days
- Stay within calorie target (±100 kcal per day)
- Respect dietary preferences and restrictions
- Provide 1-2 snacks per day (100-200 kcal each)

Return ONLY the JSON, no other text."""

        user_prompt = f"""Create a {num_days}-day meal plan with these requirements:

Dietary Preference: {dietary_preference}
Daily Calorie Target: {calorie_target} kcal
Restrictions/Allergies: {', '.join(restrictions) if restrictions else 'None'}

Start date: {start.isoformat()}

Generate diverse, balanced meals that meet nutritional needs while being enjoyable and practical to prepare."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        logger.info("Generating %d-day meal plan (%s, %d kcal)", num_days, dietary_preference, calorie_target)

        response = self.llm.invoke(messages)
        content = response.content

        # Parse JSON response
        try:
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)

            # Convert to DayPlan objects
            days = []
            for i, day_data in enumerate(data["days"]):
                day_date = (start + timedelta(days=i)).isoformat()

                breakfast = Meal(**day_data["breakfast"])
                lunch = Meal(**day_data["lunch"])
                dinner = Meal(**day_data["dinner"])
                snacks = [Meal(**s) for s in day_data.get("snacks", [])]

                days.append(DayPlan(
                    date=day_date,
                    breakfast=breakfast,
                    lunch=lunch,
                    dinner=dinner,
                    snacks=snacks,
                ))

            meal_plan = MealPlan(
                days=days,
                dietary_preference=dietary_preference,
                calorie_target=calorie_target,
                restrictions=restrictions,
            )

            logger.info("Successfully generated %d-day meal plan", len(days))
            return meal_plan

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error("Failed to parse meal plan JSON: %s", e)
            logger.debug("LLM response: %s", content[:500])
            raise ValueError(f"Failed to generate valid meal plan: {e}")
