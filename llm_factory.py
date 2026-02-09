"""LLM factory for creating chat models from different providers.

Supports Anthropic Claude and OpenAI GPT models with consistent interface.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel

from config import get_settings

logger = logging.getLogger(__name__)


def create_chat_llm(
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: str | None = None,
) -> BaseChatModel:
    """Create a chat LLM instance based on configured provider.

    Args:
        temperature: Override default temperature (0.0-1.0).
        max_tokens: Override default max tokens.
        model: Override default model name.

    Returns:
        LangChain chat model instance (ChatAnthropic or ChatOpenAI).

    Raises:
        ValueError: If provider is not supported or API key is missing.
    """
    settings = get_settings()

    # Use overrides or defaults from settings
    temp = temperature if temperature is not None else settings.llm_temperature
    tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens
    model_name = model or settings.llm_model

    provider = settings.llm_provider

    if provider == "anthropic":
        if not settings.has_anthropic_key():
            raise ValueError(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env"
            )

        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(
            model=model_name,
            api_key=settings.anthropic_api_key.get_secret_value(),
            max_tokens=tokens,
            temperature=temp,
        )
        logger.info("Created ChatAnthropic with model: %s", model_name)
        return llm

    elif provider == "openai":
        if not settings.has_openai_key():
            raise ValueError(
                "OpenAI API key not configured. Set OPENAI_API_KEY in .env"
            )

        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key.get_secret_value(),
            max_tokens=tokens,
            temperature=temp,
        )
        logger.info("Created ChatOpenAI with model: %s", model_name)
        return llm

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: anthropic, openai"
        )


def get_recommended_models() -> dict[str, list[dict[str, Any]]]:
    """Get recommended models for each provider.

    Returns:
        Dict mapping provider to list of model info dicts.
    """
    return {
        "anthropic": [
            {
                "name": "claude-sonnet-4-20250514",
                "display": "Claude Sonnet 4.5",
                "cost_per_mtok": {"input": 3.0, "output": 15.0},
                "recommended": True,
                "description": "Best balance of intelligence and cost",
            },
            {
                "name": "claude-opus-4-20250514",
                "display": "Claude Opus 4.6",
                "cost_per_mtok": {"input": 15.0, "output": 75.0},
                "recommended": False,
                "description": "Most capable, highest cost",
            },
            {
                "name": "claude-haiku-4-5-20251001",
                "display": "Claude Haiku 4.5",
                "cost_per_mtok": {"input": 0.8, "output": 4.0},
                "recommended": False,
                "description": "Fastest, lowest cost",
            },
        ],
        "openai": [
            {
                "name": "gpt-4o",
                "display": "GPT-4o",
                "cost_per_mtok": {"input": 2.5, "output": 10.0},
                "recommended": True,
                "description": "Most capable OpenAI model",
            },
            {
                "name": "gpt-4o-mini",
                "display": "GPT-4o Mini",
                "cost_per_mtok": {"input": 0.15, "output": 0.6},
                "recommended": True,
                "description": "Fast and cheap, good for most tasks",
            },
            {
                "name": "gpt-4-turbo",
                "display": "GPT-4 Turbo",
                "cost_per_mtok": {"input": 10.0, "output": 30.0},
                "recommended": False,
                "description": "Previous generation flagship",
            },
        ],
    }


def estimate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Estimate cost for a given number of tokens.

    Args:
        provider: LLM provider (anthropic, openai).
        model: Model name.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.

    Returns:
        Estimated cost in USD.
    """
    models = get_recommended_models()
    for model_info in models.get(provider, []):
        if model_info["name"] == model:
            input_cost = (input_tokens / 1_000_000) * model_info["cost_per_mtok"]["input"]
            output_cost = (output_tokens / 1_000_000) * model_info["cost_per_mtok"]["output"]
            return input_cost + output_cost

    # Fallback if model not found
    logger.warning("Cost data not found for %s/%s", provider, model)
    return 0.0
