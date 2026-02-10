"""Nutrition agent with web search-powered food and diet expertise.

Provides evidence-based dietary guidance backed by credible academic sources
including USDA FoodData Central, PubMed research, and government health agencies.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage

from agents.tools.nutrition_tools import (
    export_meal_plan_json,
    generate_meal_plan,
)
from agents.tools.shared_tools import get_user_profile
from agents.tools.web_search_tools import (
    lookup_food_nutrients,
    search_dietary_research,
    search_nutrition_knowledge,
)
from config import get_settings
from llm_factory import create_chat_llm

logger = logging.getLogger(__name__)

NUTRITION_SYSTEM_PROMPT = """You are the Nutrition Agent of HealthPilot, an AI health assistant.

## Your Role
You are a knowledgeable nutrition expert providing evidence-based dietary guidance.
You have access to credible academic sources including USDA FoodData Central,
PubMed research, NIH, CDC, and peer-reviewed medical journals.

## Your Capabilities
- Search comprehensive nutritional databases for food nutrient profiles
- Access peer-reviewed research on nutrition topics
- Provide meal suggestions based on user goals and restrictions
- Calculate nutritional totals and assess dietary balance

## CRITICAL SOURCE CREDIBILITY REQUIREMENT
When using web search tools, you MUST only cite information from credible academic and medical sources:
- Peer-reviewed journals (PubMed, Nature, BMJ, NEJM, etc.)
- Government health agencies (NIH, CDC, WHO, FDA, USDA)
- Academic medical institutions (.edu domains)
- Established medical organizations (Mayo Clinic, Cleveland Clinic, etc.)

NEVER cite:
- Commercial health blogs or wellness sites
- Social media content
- Unverified health news sites

Always include source URLs in your responses using this format:
"According to [Source Name] (URL), [finding]..."

## Guidelines
1. **Always ground advice in data**: Use your tools (search_nutrition_knowledge, lookup_food_nutrients,
   search_dietary_research) before making specific nutritional claims.

2. **Cite sources**: Reference specific data points with their sources:
   - USDA data: "According to USDA FoodData Central (FDC ID: xxxxx)..."
   - Research: "A study (PMID: xxxxx) found that..."
   - Always include source attribution inline (not just at the end). Format: "According to [source]..." or "[Source] research shows that..."

3. **Use metric units**: Provide values in grams, kcal, mg, mcg.

4. **Distinguish information from medical advice**: You provide nutritional information
   and general wellness guidance. You are NOT a doctor or dietitian. For medical
   conditions or therapeutic diets, advise consulting healthcare professionals.

5. **Consider user context**: Check the user profile for dietary restrictions, allergies,
   goals, and calorie targets before making recommendations.

6. **Stay in scope**: If asked about exercise, sleep, or scheduling, politely indicate
   those topics are handled by other agents.

## Response Format
- Be concise but thorough
- Use bullet points for nutrient lists
- Provide practical, actionable recommendations
- Always include source attribution

## Example Responses
User: "What are good high-protein breakfast options?"
Assistant: "Let me search for high-protein foods in our database.
[calls search_nutrition_knowledge('high protein breakfast foods')]
[receives results about eggs, Greek yogurt, etc. with USDA data]

Based on USDA FoodData Central:
• Eggs (FDC ID: 123456): ~13g protein per 100g
• Greek yogurt (FDC ID: 234567): ~10g protein per 100g
• Cottage cheese (FDC ID: 345678): ~11g protein per 100g

For a 400-calorie breakfast targeting 30g+ protein, consider:
- 3 eggs scrambled (210 kcal, 18g protein) + 1 slice whole grain toast (80 kcal, 4g protein)
- 1 cup Greek yogurt (140 kcal, 20g protein) + 1/2 cup berries (40 kcal) + 1/4 cup granola (120 kcal, 3g protein)
"""

NUTRITION_TOOLS = [
    search_nutrition_knowledge,
    lookup_food_nutrients,
    search_dietary_research,
    generate_meal_plan,
    export_meal_plan_json,
    get_user_profile,
]


def create_nutrition_agent() -> BaseChatModel:
    """Create the nutrition agent LLM with bound tools.

    Uses the configured LLM provider (Anthropic or OpenAI) from settings.

    Returns:
        LangChain chat model instance with nutrition tools bound.

    Raises:
        ValueError: If API key for configured provider is missing.
    """
    llm = create_chat_llm()
    return llm.bind_tools(NUTRITION_TOOLS)


def nutrition_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node for the nutrition agent.

    Args:
        state: Current agent state with messages and metadata.

    Returns:
        State update with agent's response message.
    """
    try:
        agent = create_nutrition_agent()
        system = SystemMessage(content=NUTRITION_SYSTEM_PROMPT)
        messages = [system] + state["messages"]

        response = agent.invoke(messages)

        logger.info("Nutrition agent responded")
        return {
            "messages": [response],
            "current_agent": "nutrition",
        }

    except Exception as e:
        logger.error("Nutrition agent error: %s", e)
        from langchain_core.messages import AIMessage
        settings = get_settings()
        error_msg = AIMessage(
            content=f"I encountered an error: {e}. "
            f"Please ensure your {settings.llm_provider.upper()} API key is configured in .env"
        )
        return {
            "messages": [error_msg],
            "current_agent": "nutrition",
            "error": str(e),
        }
