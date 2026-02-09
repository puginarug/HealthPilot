"""Nutrition calculator for BMR, TDEE, and macronutrient recommendations.

Based on scientifically validated formulas and literature.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Sex(str, Enum):
    """Biological sex for BMR calculations."""

    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """Activity level multipliers for TDEE calculation."""

    SEDENTARY = "sedentary"  # Little or no exercise
    LIGHTLY_ACTIVE = "lightly_active"  # Light exercise 1-3 days/week
    MODERATELY_ACTIVE = "moderately_active"  # Moderate exercise 3-5 days/week
    VERY_ACTIVE = "very_active"  # Hard exercise 6-7 days/week
    EXTREMELY_ACTIVE = "extremely_active"  # Very hard exercise & physical job


class Goal(str, Enum):
    """Nutritional goal for calorie adjustment."""

    WEIGHT_LOSS = "weight_loss"  # Caloric deficit
    MAINTENANCE = "maintenance"  # Maintain current weight
    MUSCLE_GAIN = "muscle_gain"  # Caloric surplus


@dataclass
class NutritionRecommendations:
    """Calculated nutrition recommendations."""

    bmr: int  # Basal Metabolic Rate (kcal/day)
    tdee: int  # Total Daily Energy Expenditure (kcal/day)
    target_calories: int  # Adjusted for goal (kcal/day)
    protein_min_g: float  # Minimum protein (g/day)
    protein_max_g: float  # Maximum protein (g/day)
    protein_recommended_g: float  # Recommended protein (g/day)
    carbs_min_g: float  # Minimum carbs (g/day)
    fat_min_g: float  # Minimum fat (g/day)


class NutritionCalculator:
    """Calculate BMR, TDEE, and macronutrient recommendations."""

    # Activity level multipliers for TDEE
    ACTIVITY_MULTIPLIERS = {
        ActivityLevel.SEDENTARY: 1.2,
        ActivityLevel.LIGHTLY_ACTIVE: 1.375,
        ActivityLevel.MODERATELY_ACTIVE: 1.55,
        ActivityLevel.VERY_ACTIVE: 1.725,
        ActivityLevel.EXTREMELY_ACTIVE: 1.9,
    }

    # Goal-based calorie adjustments
    GOAL_ADJUSTMENTS = {
        Goal.WEIGHT_LOSS: -500,  # 500 kcal deficit for ~0.5 kg/week loss
        Goal.MAINTENANCE: 0,
        Goal.MUSCLE_GAIN: 300,  # 300 kcal surplus for lean gains
    }

    @staticmethod
    def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: Sex) -> int:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

        This is the most accurate equation for BMR in modern populations.

        Args:
            weight_kg: Body weight in kilograms.
            height_cm: Height in centimeters.
            age: Age in years.
            sex: Biological sex (male/female).

        Returns:
            BMR in kcal/day (rounded to nearest integer).
        """
        # Mifflin-St Jeor: BMR = (10 × weight) + (6.25 × height) - (5 × age) + s
        # where s = +5 for males, -161 for females
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)

        if sex == Sex.MALE:
            bmr += 5
        else:
            bmr -= 161

        return round(bmr)

    @staticmethod
    def calculate_tdee(bmr: int, activity_level: ActivityLevel) -> int:
        """Calculate Total Daily Energy Expenditure.

        TDEE = BMR × activity multiplier

        Args:
            bmr: Basal Metabolic Rate (kcal/day).
            activity_level: Activity level category.

        Returns:
            TDEE in kcal/day (rounded to nearest integer).
        """
        multiplier = NutritionCalculator.ACTIVITY_MULTIPLIERS[activity_level]
        return round(bmr * multiplier)

    @staticmethod
    def calculate_protein_needs(weight_kg: float, activity_level: ActivityLevel) -> tuple[float, float, float]:
        """Calculate protein requirements based on activity level.

        Based on current sports nutrition guidelines:
        - Sedentary: 0.8 g/kg (RDA minimum)
        - Light/Moderate: 1.2-1.6 g/kg
        - Very/Extremely active: 1.6-2.2 g/kg (athletes)

        Args:
            weight_kg: Body weight in kilograms.
            activity_level: Activity level category.

        Returns:
            Tuple of (minimum, maximum, recommended) protein in grams/day.
        """
        if activity_level == ActivityLevel.SEDENTARY:
            min_g = 0.8 * weight_kg
            max_g = 1.0 * weight_kg
            rec_g = 0.9 * weight_kg
        elif activity_level in (ActivityLevel.LIGHTLY_ACTIVE, ActivityLevel.MODERATELY_ACTIVE):
            min_g = 1.2 * weight_kg
            max_g = 1.6 * weight_kg
            rec_g = 1.4 * weight_kg
        else:  # VERY_ACTIVE or EXTREMELY_ACTIVE
            min_g = 1.6 * weight_kg
            max_g = 2.2 * weight_kg
            rec_g = 1.8 * weight_kg

        return round(min_g, 1), round(max_g, 1), round(rec_g, 1)

    @staticmethod
    def calculate_macros(target_calories: int, protein_g: float) -> tuple[float, float]:
        """Calculate remaining macros after protein allocation.

        Assumes:
        - Protein: 4 kcal/g
        - Carbs: 4 kcal/g (45-65% of remaining calories)
        - Fat: 9 kcal/g (20-35% of total calories)

        Args:
            target_calories: Daily calorie target.
            protein_g: Protein allocation in grams.

        Returns:
            Tuple of (minimum carbs g, minimum fat g).
        """
        protein_kcal = protein_g * 4
        remaining_kcal = target_calories - protein_kcal

        # Fat: minimum 20% of total calories for hormonal health
        min_fat_kcal = target_calories * 0.20
        min_fat_g = min_fat_kcal / 9

        # Carbs: rest of calories after protein and min fat
        carb_kcal = target_calories - protein_kcal - min_fat_kcal
        min_carbs_g = max(carb_kcal / 4, 100)  # At least 100g for brain function

        return round(min_carbs_g, 1), round(min_fat_g, 1)

    @classmethod
    def get_recommendations(
        cls,
        weight_kg: float,
        height_cm: float,
        age: int,
        sex: Sex,
        activity_level: ActivityLevel,
        goal: Goal = Goal.MAINTENANCE,
    ) -> NutritionRecommendations:
        """Get complete nutrition recommendations.

        Args:
            weight_kg: Body weight in kilograms.
            height_cm: Height in centimeters.
            age: Age in years.
            sex: Biological sex.
            activity_level: Activity level.
            goal: Nutritional goal (weight loss, maintenance, muscle gain).

        Returns:
            Complete nutrition recommendations.
        """
        # Calculate BMR and TDEE
        bmr = cls.calculate_bmr(weight_kg, height_cm, age, sex)
        tdee = cls.calculate_tdee(bmr, activity_level)

        # Adjust for goal
        adjustment = cls.GOAL_ADJUSTMENTS[goal]
        target_calories = tdee + adjustment

        # Calculate protein needs
        protein_min, protein_max, protein_rec = cls.calculate_protein_needs(weight_kg, activity_level)

        # Calculate remaining macros
        carbs_min, fat_min = cls.calculate_macros(target_calories, protein_rec)

        return NutritionRecommendations(
            bmr=bmr,
            tdee=tdee,
            target_calories=target_calories,
            protein_min_g=protein_min,
            protein_max_g=protein_max,
            protein_recommended_g=protein_rec,
            carbs_min_g=carbs_min,
            fat_min_g=fat_min,
        )
