"""Web search tools for credible academic health information.

Uses Tavily API to search only trusted academic and medical domains
including PubMed, NIH, CDC, WHO, and academic institutions.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import tool
from tavily import TavilyClient

from config import get_settings

logger = logging.getLogger(__name__)

# Academic and medical domains for credible health information
ACADEMIC_HEALTH_DOMAINS = [
    # Government Health Agencies
    "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",  # PubMed Central
    "nih.gov",
    "cdc.gov",
    "who.int",
    "fda.gov",
    "usda.gov",
    "health.gov",
    "nutrition.gov",
    # Academic Institutions
    "harvard.edu",
    "stanford.edu",
    "yale.edu",
    "mit.edu",
    "jhu.edu",  # Johns Hopkins
    "ucsd.edu",
    "ucsf.edu",
    "upenn.edu",
    # Medical Journals and Organizations
    "mayoclinic.org",
    "clevelandclinic.org",
    "bmj.com",  # British Medical Journal
    "nejm.org",  # New England Journal of Medicine
    "nature.com",
    "science.org",
    "thelancet.com",
    "jamanetwork.com",
    "annals.org",  # Annals of Internal Medicine
    # Nutrition and Exercise
    "eatright.org",  # Academy of Nutrition and Dietetics
    "acsm.org",  # American College of Sports Medicine
    "nutrition.org",  # American Society for Nutrition
    "nhlbi.nih.gov",  # National Heart, Lung, and Blood Institute
    "niddk.nih.gov",  # National Institute of Diabetes and Digestive and Kidney Diseases
]


def _get_tavily_client() -> TavilyClient:
    """Get configured Tavily client.

    Returns:
        TavilyClient instance.

    Raises:
        ValueError: If TAVILY_API_KEY not configured.
    """
    settings = get_settings()
    if not settings.has_tavily_key():
        raise ValueError(
            "Tavily API key not configured. "
            "Set TAVILY_API_KEY in .env. Visit https://tavily.com to get an API key."
        )
    return TavilyClient(api_key=settings.tavily_api_key.get_secret_value())


def _format_search_results(results: dict[str, Any], max_length: int = 3000) -> str:
    """Format Tavily search results into readable text with source attribution.

    Args:
        results: Tavily API response dictionary.
        max_length: Maximum total character length.

    Returns:
        Formatted results string with URLs and snippets.
    """
    if not results.get("results"):
        query = results.get("query", "your search")
        return (
            f"No credible academic sources found for '{query}'. "
            f"Try rephrasing your query or broadening the topic."
        )

    parts: list[str] = []
    current_length = 0

    for i, result in enumerate(results["results"], 1):
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        content = result.get("content", "")
        score = result.get("score", 0.0)

        source_info = f"[Source {i}: {title}]\nURL: {url}\nRelevance: {score:.2f}\n"

        result_text = f"{source_info}\n{content}\n"

        if current_length + len(result_text) > max_length:
            parts.append("... [additional sources truncated for length]")
            break

        parts.append(result_text)
        current_length += len(result_text)

    return "\n---\n".join(parts)


@tool
def search_nutrition_knowledge(query: str, max_results: int = 5) -> str:
    """Search credible academic sources for nutrition information.

    Searches government databases (USDA, NIH), academic institutions,
    and peer-reviewed journals for evidence-based nutrition guidance.

    Args:
        query: Nutrition topic or question (e.g., "vitamin D deficiency").
        max_results: Maximum number of sources to return (default: 5).

    Returns:
        Formatted search results with URLs and relevance scores.

    Example:
        >>> search_nutrition_knowledge("benefits of omega-3 fatty acids")
        [Source 1: Omega-3 Fatty Acids - NIH]
        URL: https://ods.od.nih.gov/factsheets/Omega3FattyAcids-HealthProfessional/
        Relevance: 0.95

        Omega-3 fatty acids are essential nutrients important for...
    """
    try:
        client = _get_tavily_client()
        results = client.search(
            query=f"nutrition {query}",
            search_depth="advanced",
            include_domains=ACADEMIC_HEALTH_DOMAINS,
            max_results=max_results,
            include_raw_content=True,
        )
        return _format_search_results(results, max_length=3000)
    except ValueError as e:
        return str(e)
    except Exception as e:
        logger.error("Nutrition knowledge search failed: %s", e)
        return f"Error searching nutrition information: {e}"


@tool
def lookup_food_nutrients(food_name: str, max_results: int = 3) -> str:
    """Look up nutritional content and data for a specific food.

    Searches USDA FoodData Central and nutrition databases for
    detailed nutrient profiles, serving sizes, and health effects.

    Args:
        food_name: Name of the food (e.g., "spinach", "salmon").
        max_results: Maximum number of sources to return (default: 3).

    Returns:
        Formatted nutrition data with sources.

    Example:
        >>> lookup_food_nutrients("quinoa")
        [Source 1: Quinoa Nutrition Facts - USDA]
        URL: https://fdc.nal.usda.gov/...
        Relevance: 0.98

        Quinoa contains 8g protein per cup cooked, all essential amino acids...
    """
    try:
        client = _get_tavily_client()
        results = client.search(
            query=f"USDA nutrition facts {food_name} nutrients calories protein",
            search_depth="advanced",
            include_domains=ACADEMIC_HEALTH_DOMAINS,
            max_results=max_results,
            include_raw_content=True,
        )
        return _format_search_results(results, max_length=2000)
    except ValueError as e:
        return str(e)
    except Exception as e:
        logger.error("Food nutrient lookup failed: %s", e)
        return f"Error looking up food nutrients: {e}"


@tool
def search_dietary_research(topic: str, max_results: int = 5) -> str:
    """Search peer-reviewed research on dietary topics.

    Searches PubMed, medical journals, and academic publications
    for evidence-based research on diet, health outcomes, and nutrition science.

    Args:
        topic: Research topic (e.g., "Mediterranean diet cardiovascular health").
        max_results: Maximum number of sources to return (default: 5).

    Returns:
        Formatted research findings with citations.

    Example:
        >>> search_dietary_research("intermittent fasting weight loss")
        [Source 1: Intermittent Fasting Effects on Weight Loss - PubMed]
        URL: https://pubmed.ncbi.nlm.nih.gov/...
        Relevance: 0.93

        Meta-analysis of 12 studies shows intermittent fasting results in...
    """
    try:
        client = _get_tavily_client()
        results = client.search(
            query=f"research study {topic} pubmed",
            search_depth="advanced",
            include_domains=ACADEMIC_HEALTH_DOMAINS,
            max_results=max_results,
            include_raw_content=True,
        )
        return _format_search_results(results, max_length=3000)
    except ValueError as e:
        return str(e)
    except Exception as e:
        logger.error("Dietary research search failed: %s", e)
        return f"Error searching dietary research: {e}"


@tool
def search_exercise_guidance(query: str, max_results: int = 5) -> str:
    """Search credible sources for exercise and fitness guidance.

    Searches CDC, ACSM (American College of Sports Medicine), academic
    institutions, and medical journals for evidence-based exercise recommendations.

    Args:
        query: Exercise topic or question (e.g., "strength training frequency").
        max_results: Maximum number of sources to return (default: 5).

    Returns:
        Formatted exercise guidance with sources.

    Example:
        >>> search_exercise_guidance("HIIT cardio benefits")
        [Source 1: High-Intensity Interval Training - Mayo Clinic]
        URL: https://www.mayoclinic.org/...
        Relevance: 0.91

        HIIT workouts improve cardiovascular fitness more efficiently...
    """
    try:
        client = _get_tavily_client()
        results = client.search(
            query=f"exercise fitness {query}",
            search_depth="advanced",
            include_domains=ACADEMIC_HEALTH_DOMAINS,
            max_results=max_results,
            include_raw_content=True,
        )
        return _format_search_results(results, max_length=3000)
    except ValueError as e:
        return str(e)
    except Exception as e:
        logger.error("Exercise guidance search failed: %s", e)
        return f"Error searching exercise guidance: {e}"


@tool
def search_wellbeing_research(topic: str, max_results: int = 5) -> str:
    """Search research on sleep, stress, mental health, and wellbeing.

    Searches NIH, CDC, academic medical centers, and psychology journals
    for evidence-based guidance on sleep hygiene, stress management, and mental health.

    Args:
        topic: Wellbeing topic (e.g., "sleep quality improvement strategies").
        max_results: Maximum number of sources to return (default: 5).

    Returns:
        Formatted research findings with sources.

    Example:
        >>> search_wellbeing_research("meditation stress reduction")
        [Source 1: Meditation for Stress Management - Harvard Health]
        URL: https://www.health.harvard.edu/...
        Relevance: 0.89

        Research shows mindfulness meditation reduces cortisol levels...
    """
    try:
        client = _get_tavily_client()
        results = client.search(
            query=f"research {topic} wellbeing health",
            search_depth="advanced",
            include_domains=ACADEMIC_HEALTH_DOMAINS,
            max_results=max_results,
            include_raw_content=True,
        )
        return _format_search_results(results, max_length=3000)
    except ValueError as e:
        return str(e)
    except Exception as e:
        logger.error("Wellbeing research search failed: %s", e)
        return f"Error searching wellbeing research: {e}"
