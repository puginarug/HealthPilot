"""USDA FoodData Central data loader.

Fetches nutritional data from the USDA FoodData Central API
and converts it to LangChain Document format for RAG.

API docs: https://fdc.nal.usda.gov/api-guide.html
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from langchain_core.documents import Document
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings

logger = logging.getLogger(__name__)

USDA_API_BASE = "https://api.nal.usda.gov/fdc/v1"


class USDALoader:
    """Load USDA FoodData Central data into Document objects.

    Fetches common foods with their nutritional profiles.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the USDA loader.

        Args:
            api_key: USDA API key (optional, uses DEMO_KEY with rate limits if not provided).
        """
        settings = get_settings()
        self.api_key = (
            api_key
            or settings.usda_api_key.get_secret_value()
            or "DEMO_KEY"
        )
        if self.api_key == "DEMO_KEY":
            logger.warning(
                "Using DEMO_KEY for USDA API (rate limited to 30 requests/hour). "
                "Get a free key at https://fdc.nal.usda.gov/api-key-signup.html"
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _api_request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Make a rate-limited API request to USDA FoodData Central.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            JSON response as dict.
        """
        params["api_key"] = self.api_key
        url = f"{USDA_API_BASE}/{endpoint}"

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def load(self, limit: int = 1000, data_type: str = "Foundation") -> list[Document]:
        """Load USDA foods and convert to Document objects.

        Args:
            limit: Maximum number of foods to fetch.
            data_type: Food data type ('Foundation', 'SR Legacy', or 'Survey (FNDDS)').

        Returns:
            List of Document objects, each representing one food item.
        """
        logger.info("Fetching %d USDA foods (dataType: %s)...", limit, data_type)

        # Search for foods
        try:
            search_result = self._api_request(
                "foods/search",
                {
                    "dataType": data_type,
                    "pageSize": min(limit, 200),  # API max is 200 per page
                    "sortBy": "dataType.keyword",
                    "sortOrder": "asc",
                },
            )
        except Exception as e:
            logger.error("Failed to fetch USDA data: %s", e)
            return []

        foods = search_result.get("foods", [])
        logger.info("Retrieved %d foods from USDA API", len(foods))

        documents: list[Document] = []

        for food in foods[:limit]:
            try:
                doc = self._convert_food_to_document(food)
                documents.append(doc)
            except Exception as e:
                logger.warning("Failed to process food %s: %s", food.get("fdcId"), e)

            # Rate limiting for DEMO_KEY
            if self.api_key == "DEMO_KEY":
                time.sleep(0.1)

        logger.info("Converted %d foods to documents", len(documents))
        return documents

    def _convert_food_to_document(self, food: dict[str, Any]) -> Document:
        """Convert a single USDA food item to a LangChain Document.

        Args:
            food: Food data from USDA API.

        Returns:
            Document with formatted nutritional info.
        """
        fdc_id = food.get("fdcId")
        description = food.get("description", "Unknown food")
        category = food.get("foodCategory", "N/A")

        # Extract nutrients
        nutrients = food.get("foodNutrients", [])
        nutrient_lines: list[str] = []

        # Prioritize key nutrients
        priority_nutrients = {
            "Protein", "Total lipid (fat)", "Carbohydrate, by difference",
            "Energy", "Fiber, total dietary", "Sugars, total including NLEA",
            "Calcium, Ca", "Iron, Fe", "Sodium, Na", "Vitamin C, total ascorbic acid",
            "Vitamin A, RAE", "Cholesterol",
        }

        for nutrient in nutrients:
            name = nutrient.get("nutrientName", "")
            value = nutrient.get("value")
            unit = nutrient.get("unitName", "")

            if value is not None and (name in priority_nutrients or len(nutrient_lines) < 15):
                nutrient_lines.append(f"{name}: {value}{unit}")

        # Format document text
        text_parts = [
            f"Food: {description}",
            f"Category: {category}",
            "Nutrients per 100g:",
        ]
        text_parts.extend(nutrient_lines)

        page_content = "\n".join(text_parts)

        metadata = {
            "source": "usda",
            "fdc_id": str(fdc_id),
            "food_category": category,
            "description": description,
        }

        return Document(page_content=page_content, metadata=metadata)
