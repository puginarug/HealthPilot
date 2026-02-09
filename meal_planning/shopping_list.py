"""Shopping list generation from meal plans.

Parses ingredients, aggregates quantities, and organizes by category.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from meal_planning.generator import MealPlan


@dataclass
class ShoppingItem:
    """Single item on shopping list."""

    name: str  # "Greek yogurt"
    quantity: float  # 4.5
    unit: str  # "cups"
    category: str  # "Dairy"
    meal_sources: list[str]  # ["Breakfast Day 1", "Snack Day 2"]


@dataclass
class ShoppingList:
    """Complete shopping list from meal plan."""

    items_by_category: dict[str, list[ShoppingItem]]
    total_items: int
    meal_plan_days: int
    dietary_preference: str
    generated_date: str


# Category mappings for ingredient classification
CATEGORY_KEYWORDS = {
    "Produce": [
        "apple", "banana", "orange", "berry", "berries", "strawberr", "blueberr", "raspberr",
        "lettuce", "spinach", "kale", "arugula", "tomato", "cucumber", "carrot", "broccoli",
        "bell pepper", "onion", "garlic", "ginger", "lemon", "lime", "avocado", "zucchini",
        "mushroom", "celery", "parsley", "cilantro", "basil", "potato", "sweet potato",
    ],
    "Proteins": [
        "chicken", "beef", "pork", "turkey", "fish", "salmon", "tuna", "shrimp", "tofu",
        "tempeh", "egg", "lentil", "bean", "chickpea", "edamame",
    ],
    "Dairy": [
        "milk", "yogurt", "cheese", "butter", "cream", "sour cream", "cottage cheese",
        "mozzarella", "cheddar", "parmesan", "feta", "ricotta",
    ],
    "Grains": [
        "bread", "rice", "pasta", "quinoa", "oats", "oatmeal", "cereal", "flour", "tortilla",
        "pita", "bagel", "couscous", "barley", "bulgur",
    ],
    "Pantry": [
        "oil", "olive oil", "vegetable oil", "vinegar", "balsamic", "soy sauce", "salt",
        "pepper", "sugar", "honey", "maple syrup", "spice", "cumin", "paprika", "cinnamon",
        "vanilla", "baking powder", "baking soda", "stock", "broth",
    ],
    "Nuts & Seeds": [
        "almond", "walnut", "cashew", "peanut", "peanut butter", "almond butter", "seed",
        "sunflower", "pumpkin seed", "chia", "flax",
    ],
    "Beverages": [
        "coffee", "tea", "juice", "water", "milk", "almond milk", "soy milk", "coconut milk",
    ],
}


def parse_ingredient(ingredient_str: str) -> dict[str, any]:
    """Parse ingredient string into quantity, unit, and name.

    Examples:
        "2 cups Greek yogurt" → {"qty": 2.0, "unit": "cups", "name": "Greek yogurt"}
        "1.5 lbs chicken breast" → {"qty": 1.5, "unit": "lbs", "name": "chicken breast"}
        "3 large eggs" → {"qty": 3.0, "unit": "large", "name": "eggs"}
        "Salt to taste" → {"qty": 1.0, "unit": "to taste", "name": "Salt"}

    Args:
        ingredient_str: Raw ingredient string.

    Returns:
        Dictionary with qty, unit, and name.
    """
    ingredient_str = ingredient_str.strip()

    # Pattern: optional quantity, optional unit, required name
    # Handles: "2 cups yogurt", "1.5 lbs chicken", "3 eggs", "Salt to taste"
    pattern = r"^(\d+\.?\d*|\d+/\d+)?\s*([a-zA-Z]+\s+[a-zA-Z]+|[a-zA-Z]+)?\s*(.+)$"
    match = re.match(pattern, ingredient_str)

    if match:
        qty_str, unit, name = match.groups()

        # Parse quantity (default 1.0 if not specified)
        if qty_str:
            # Handle fractions like "1/2"
            if "/" in qty_str:
                num, denom = qty_str.split("/")
                qty = float(num) / float(denom)
            else:
                qty = float(qty_str)
        else:
            qty = 1.0

        # Clean unit (default "item" if not specified)
        unit = unit.strip() if unit else "item"

        # Clean name
        name = name.strip()

        return {"qty": qty, "unit": unit, "name": name}
    else:
        # Fallback for unparseable strings
        return {"qty": 1.0, "unit": "item", "name": ingredient_str}


def categorize_ingredient(ingredient_name: str) -> str:
    """Categorize ingredient based on name keywords.

    Args:
        ingredient_name: Name of the ingredient.

    Returns:
        Category name (Produce, Proteins, Dairy, etc.) or "Other".
    """
    ingredient_lower = ingredient_name.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in ingredient_lower:
                return category

    return "Other"


def generate_shopping_list(meal_plan: MealPlan) -> ShoppingList:
    """Generate organized shopping list from meal plan.

    Args:
        meal_plan: Complete meal plan with all days and meals.

    Returns:
        Shopping list organized by category.
    """
    # Aggregate ingredients: key = (name, unit), value = {qty, sources}
    aggregated = defaultdict(lambda: {"qty": 0.0, "sources": []})

    for day_idx, day in enumerate(meal_plan.days, 1):
        day_label = f"Day {day_idx}"

        # Process all meals
        all_meals = [
            ("Breakfast", day.breakfast),
            ("Lunch", day.lunch),
            ("Dinner", day.dinner),
        ]

        for snack_idx, snack in enumerate(day.snacks, 1):
            all_meals.append((f"Snack {snack_idx}", snack))

        for meal_type, meal in all_meals:
            for ingredient_str in meal.ingredients:
                parsed = parse_ingredient(ingredient_str)

                # Use (name, unit) as key for aggregation
                key = (parsed["name"], parsed["unit"])
                aggregated[key]["qty"] += parsed["qty"]
                aggregated[key]["sources"].append(f"{meal_type} {day_label}")

    # Convert to ShoppingItem objects and categorize
    items_by_category = defaultdict(list)

    for (name, unit), data in aggregated.items():
        category = categorize_ingredient(name)

        item = ShoppingItem(
            name=name,
            quantity=data["qty"],
            unit=unit,
            category=category,
            meal_sources=data["sources"],
        )

        items_by_category[category].append(item)

    # Sort items within each category alphabetically
    for category in items_by_category:
        items_by_category[category].sort(key=lambda x: x.name)

    # Sort categories for consistent display
    sorted_categories = dict(sorted(items_by_category.items()))

    total_items = sum(len(items) for items in sorted_categories.values())

    return ShoppingList(
        items_by_category=sorted_categories,
        total_items=total_items,
        meal_plan_days=len(meal_plan.days),
        dietary_preference=meal_plan.dietary_preference,
        generated_date=date.today().isoformat(),
    )
