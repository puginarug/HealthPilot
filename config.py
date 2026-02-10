"""Centralized configuration for HealthPilot.

Loads settings from environment variables and .env file using pydantic-settings.
All API keys use SecretStr to prevent accidental logging exposure.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file.

    Environment variables take precedence over .env file values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM ---
    llm_provider: Literal["anthropic", "openai"] = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"  # or gpt-4o-mini, gpt-4o, etc.
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.3

    # Anthropic
    anthropic_api_key: SecretStr = Field(default=SecretStr(""))

    # OpenAI (also used for chat if llm_provider="openai")
    openai_api_key: SecretStr = Field(default=SecretStr(""))

    # --- Embeddings ---
    openai_embedding_model: str = "text-embedding-3-small"

    # --- Vector Store ---
    chroma_persist_directory: Path = Path("./data/chroma_db")
    chroma_collection_nutrition: str = "nutrition_docs"
    chroma_collection_pubmed: str = "pubmed_abstracts"

    # --- Google Calendar ---
    google_credentials_path: Path = Path("./credentials/google_credentials.json")
    google_calendar_id: str = "primary"

    # --- LangSmith Observability ---
    # LangSmith uses LANGSMITH_API_KEY as of 2024+
    langsmith_api_key: SecretStr = Field(default=SecretStr(""))
    langchain_tracing_v2: bool = False
    langchain_project: str = "healthpilot"

    # --- USDA ---
    usda_api_key: SecretStr = Field(default=SecretStr(""))

    # --- Tavily Web Search ---
    tavily_api_key: SecretStr = Field(default=SecretStr(""))

    # --- Data ---
    sample_data_dir: Path = Path("./data/sample")
    user_profile_path: Path = Path("./data/user_profile.json")

    # --- App ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    def has_anthropic_key(self) -> bool:
        """Check if a valid Anthropic API key is configured."""
        return bool(self.anthropic_api_key.get_secret_value())

    def has_openai_key(self) -> bool:
        """Check if a valid OpenAI API key is configured."""
        return bool(self.openai_api_key.get_secret_value())

    def has_llm_key(self) -> bool:
        """Check if the configured LLM provider has an API key."""
        if self.llm_provider == "anthropic":
            return self.has_anthropic_key()
        elif self.llm_provider == "openai":
            return self.has_openai_key()
        return False

    def has_langsmith(self) -> bool:
        """Check if LangSmith tracing is configured."""
        return self.langchain_tracing_v2 and bool(
            self.langsmith_api_key.get_secret_value()
        )

    def has_tavily_key(self) -> bool:
        """Check if a valid Tavily API key is configured."""
        return bool(self.tavily_api_key.get_secret_value())


# Module-level singleton
_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the cached settings singleton.

    Returns:
        The application Settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset the settings singleton. Useful for testing."""
    global _settings
    _settings = None


def setup_logging() -> None:
    """Configure application-wide logging. Call once at startup."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    # Suppress noisy third-party loggers
    for logger_name in ("httpx", "chromadb", "streamlit", "httpcore", "urllib3"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def setup_langsmith() -> None:
    """Configure LangSmith tracing if enabled.

    LangChain reads from environment variables, so we need to set them explicitly.
    Call this once at startup, before creating any LLM instances.
    """
    settings = get_settings()

    if settings.has_langsmith():
        # Set environment variables for LangChain to pick up
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.get_secret_value()
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

        logger = logging.getLogger(__name__)
        logger.info("LangSmith tracing enabled for project: %s", settings.langchain_project)
    else:
        # Ensure tracing is disabled if not configured
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
