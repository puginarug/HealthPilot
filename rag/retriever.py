"""RAG retriever with ChromaDB and semantic search.

Provides document retrieval from nutrition and research knowledge bases
with source attribution and score-based ranking.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from config import get_settings

logger = logging.getLogger(__name__)

CollectionName = Literal["nutrition_docs", "pubmed_abstracts"]


class VectorStoreManager:
    """Manage ChromaDB collections for the RAG pipeline.

    Uses persistent local storage via ChromaDB. Embedding model is
    OpenAI text-embedding-3-small (1536 dimensions).
    """

    def __init__(self) -> None:
        settings = get_settings()

        if not settings.has_openai_key():
            logger.warning("OpenAI API key not configured - embeddings will fail")

        self._embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key.get_secret_value() if settings.has_openai_key() else "dummy",
        )

        persist_dir = settings.chroma_persist_directory
        persist_dir.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info("Initialized ChromaDB at %s", persist_dir)

    def get_or_create_collection(self, name: str) -> Chroma:
        """Get or create a ChromaDB collection wrapped in LangChain Chroma.

        Args:
            name: Collection name (e.g., 'nutrition_docs').

        Returns:
            LangChain Chroma vectorstore instance.
        """
        return Chroma(
            client=self._client,
            collection_name=name,
            embedding_function=self._embeddings,
        )

    def add_documents(
        self,
        collection_name: str,
        documents: list[Document],
        batch_size: int = 100,
    ) -> None:
        """Add documents to a collection in batches.

        Args:
            collection_name: Target collection name.
            documents: List of LangChain Document objects.
            batch_size: Documents to process at once (avoid memory issues).
        """
        collection = self.get_or_create_collection(collection_name)
        total = len(documents)

        for i in range(0, total, batch_size):
            batch = documents[i : i + batch_size]
            collection.add_documents(batch)
            logger.info(
                "Added batch %d-%d/%d to %s",
                i + 1,
                min(i + batch_size, total),
                total,
                collection_name,
            )

        logger.info("Finished adding %d documents to %s", total, collection_name)

    def collection_stats(self, name: str) -> dict[str, int]:
        """Get statistics for a collection.

        Args:
            name: Collection name.

        Returns:
            Dictionary with 'count' key.
        """
        try:
            collection = self._client.get_collection(name)
            return {"count": collection.count()}
        except Exception:
            return {"count": 0}

    def delete_collection(self, name: str) -> None:
        """Delete a collection entirely.

        Args:
            name: Collection name to delete.
        """
        try:
            self._client.delete_collection(name)
            logger.info("Deleted collection: %s", name)
        except Exception as e:
            logger.warning("Failed to delete collection %s: %s", name, e)


class HealthRetriever:
    """Retrieve relevant documents from the RAG knowledge base.

    Supports searching single or multiple collections with score-based
    reranking and deduplication.
    """

    def __init__(
        self,
        store_manager: VectorStoreManager | None = None,
        top_k: int = 5,
    ) -> None:
        """Initialize the retriever.

        Args:
            store_manager: VectorStoreManager instance (creates one if None).
            top_k: Default number of results to return.
        """
        self._store = store_manager or VectorStoreManager()
        self._top_k = top_k

    def retrieve(
        self,
        query: str,
        collections: list[CollectionName] | None = None,
        top_k: int | None = None,
    ) -> list[Document]:
        """Retrieve documents relevant to the query.

        Searches across specified collections, merges results, deduplicates,
        and returns top-k by relevance score.

        Args:
            query: Search query string.
            collections: Which collections to search (defaults to all).
            top_k: Number of results to return.

        Returns:
            List of Document objects sorted by relevance.
        """
        collections = collections or ["nutrition_docs", "pubmed_abstracts"]
        k = top_k or self._top_k
        all_results: list[tuple[Document, float]] = []

        for coll_name in collections:
            try:
                vectorstore = self._store.get_or_create_collection(coll_name)
                results = vectorstore.similarity_search_with_relevance_scores(
                    query, k=k
                )
                for doc, score in results:
                    doc.metadata["_collection"] = coll_name
                    doc.metadata["_relevance_score"] = score
                    all_results.append((doc, score))
            except Exception as e:
                logger.warning("Failed to search collection %s: %s", coll_name, e)

        if not all_results:
            logger.info("No results found for query: %s", query[:50])
            return []

        # Sort by relevance descending, deduplicate by content prefix
        all_results.sort(key=lambda x: x[1], reverse=True)
        seen_content: set[str] = set()
        unique_results: list[Document] = []

        for doc, _score in all_results:
            content_hash = doc.page_content[:150]  # Use first 150 chars as fingerprint
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(doc)
            if len(unique_results) >= k:
                break

        logger.info("Retrieved %d documents for query: %s...", len(unique_results), query[:50])
        return unique_results

    def format_context(self, documents: list[Document], max_length: int = 4000) -> str:
        """Format retrieved documents into a context string for LLM prompts.

        Includes source attribution and truncates if needed.

        Args:
            documents: Retrieved Document objects.
            max_length: Maximum total character length.

        Returns:
            Formatted context string.
        """
        if not documents:
            return "No relevant documents found."

        parts: list[str] = []
        current_length = 0

        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "unknown")
            score = doc.metadata.get("_relevance_score", 0.0)

            source_info = f"[Source {i} ({source}, relevance: {score:.2f})]"
            content = doc.page_content

            # Add metadata hints
            if source == "usda":
                fdc_id = doc.metadata.get("fdc_id", "")
                if fdc_id:
                    source_info += f" [USDA FDC ID: {fdc_id}]"
            elif source == "pubmed":
                pmid = doc.metadata.get("pmid", "")
                title = doc.metadata.get("title", "")
                if pmid:
                    source_info += f" [PMID: {pmid}]"
                if title:
                    source_info = f"{source_info}\nTitle: {title}"

            doc_text = f"{source_info}\n{content}\n"

            if current_length + len(doc_text) > max_length:
                parts.append("... [additional sources truncated for length]")
                break

            parts.append(doc_text)
            current_length += len(doc_text)

        return "\n---\n".join(parts)
