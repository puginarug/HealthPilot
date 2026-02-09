"""CLI for ingesting documents into the RAG knowledge base.

Usage:
    python -m rag.ingest --source usda --limit 1000
    python -m rag.ingest --source pubmed --limit 500
    python -m rag.ingest --source all
"""

from __future__ import annotations

import argparse
import logging
import sys

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_settings, setup_logging
from rag.retriever import VectorStoreManager
from rag.sources.pubmed_loader import PubMedLoader
from rag.sources.usda_loader import USDALoader

logger = logging.getLogger(__name__)


def ingest_usda(limit: int = 1000) -> None:
    """Ingest USDA FoodData Central data.

    Args:
        limit: Maximum number of foods to ingest.
    """
    logger.info("=== Ingesting USDA FoodData Central ===")

    # Load documents
    loader = USDALoader()
    documents = loader.load(limit=limit)

    if not documents:
        logger.error("No USDA documents loaded. Check API key and network.")
        return

    # Chunk documents (though USDA entries are already concise)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(documents)
    logger.info("Split into %d chunks", len(chunks))

    # Add to vector store
    settings = get_settings()
    if not settings.has_openai_key():
        logger.error("OpenAI API key not configured. Cannot create embeddings.")
        logger.info("Set OPENAI_API_KEY in your .env file.")
        return

    store = VectorStoreManager()
    store.add_documents(settings.chroma_collection_nutrition, chunks)

    stats = store.collection_stats(settings.chroma_collection_nutrition)
    logger.info("USDA ingestion complete. Collection now has %d documents.", stats["count"])


def ingest_pubmed(limit_per_query: int = 100) -> None:
    """Ingest PubMed research abstracts.

    Args:
        limit_per_query: Max results per search query.
    """
    logger.info("=== Ingesting PubMed Abstracts ===")

    # Load documents
    loader = PubMedLoader()
    documents = loader.load(max_results_per_query=limit_per_query)

    if not documents:
        logger.error("No PubMed documents loaded. Check network connection.")
        return

    # Chunk abstracts
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(documents)
    logger.info("Split into %d chunks", len(chunks))

    # Add to vector store
    settings = get_settings()
    if not settings.has_openai_key():
        logger.error("OpenAI API key not configured. Cannot create embeddings.")
        logger.info("Set OPENAI_API_KEY in your .env file.")
        return

    store = VectorStoreManager()
    store.add_documents(settings.chroma_collection_pubmed, chunks)

    stats = store.collection_stats(settings.chroma_collection_pubmed)
    logger.info("PubMed ingestion complete. Collection now has %d documents.", stats["count"])


def show_stats() -> None:
    """Display current collection statistics."""
    logger.info("=== RAG Collection Statistics ===")
    settings = get_settings()
    store = VectorStoreManager()

    nutrition_stats = store.collection_stats(settings.chroma_collection_nutrition)
    pubmed_stats = store.collection_stats(settings.chroma_collection_pubmed)

    logger.info("USDA Nutrition: %d documents", nutrition_stats["count"])
    logger.info("PubMed Research: %d documents", pubmed_stats["count"])
    logger.info("Total: %d documents", nutrition_stats["count"] + pubmed_stats["count"])


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest documents into HealthPilot RAG knowledge base"
    )
    parser.add_argument(
        "--source",
        choices=["usda", "pubmed", "all"],
        required=True,
        help="Which data source to ingest",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum documents to ingest (for USDA) or per-query (for PubMed)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show collection statistics only",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(message)s")
    else:
        setup_logging()

    if args.stats:
        show_stats()
        return 0

    # Check API keys
    settings = get_settings()
    if not settings.has_openai_key():
        logger.error("OPENAI_API_KEY not configured. Add it to your .env file.")
        logger.info("Get a free key at https://platform.openai.com/api-keys")
        return 1

    # Ingest
    try:
        if args.source == "usda" or args.source == "all":
            ingest_usda(limit=args.limit)

        if args.source == "pubmed" or args.source == "all":
            # For pubmed, limit is per-query (default queries = 6)
            limit_per_query = args.limit // 6 if args.source == "all" else args.limit
            ingest_pubmed(limit_per_query=max(limit_per_query, 50))

        show_stats()
        logger.info("Ingestion complete!")
        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception("Ingestion failed: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
