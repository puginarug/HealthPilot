"""PubMed abstract loader using NCBI E-utilities.

Fetches research abstracts from PubMed and converts them to
LangChain Document format for RAG.

API docs: https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx
from langchain_core.documents import Document
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


class PubMedLoader:
    """Load PubMed abstracts into Document objects.

    Uses NCBI E-utilities API (free, rate-limited to 3 requests/second).
    """

    def __init__(self, email: str = "healthpilot@example.com") -> None:
        """Initialize the PubMed loader.

        Args:
            email: Contact email for NCBI (required for API compliance).
        """
        self.email = email
        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Enforce 3 requests/second rate limit."""
        elapsed = time.time() - self._last_request_time
        if elapsed < 0.34:  # ~3 requests/sec
            time.sleep(0.34 - elapsed)
        self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _esearch(self, query: str, max_results: int = 500) -> list[str]:
        """Search PubMed for PMIDs matching the query.

        Args:
            query: PubMed search query.
            max_results: Maximum PMIDs to return.

        Returns:
            List of PMIDs as strings.
        """
        self._rate_limit()

        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "email": self.email,
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.get(PUBMED_ESEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()

        pmids = data.get("esearchresult", {}).get("idlist", [])
        logger.info("Found %d PMIDs for query: %s", len(pmids), query[:50])
        return pmids

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _efetch(self, pmids: list[str]) -> str:
        """Fetch article details for a list of PMIDs.

        Args:
            pmids: List of PubMed IDs.

        Returns:
            XML string with article data.
        """
        self._rate_limit()

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "email": self.email,
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.get(PUBMED_EFETCH_URL, params=params)
            response.raise_for_status()
            return response.text

    def load(
        self,
        queries: list[str] | None = None,
        max_results_per_query: int = 100,
    ) -> list[Document]:
        """Load PubMed abstracts for given queries.

        Args:
            queries: List of search queries. Defaults to nutrition/exercise topics.
            max_results_per_query: Max abstracts to fetch per query.

        Returns:
            List of Document objects, each representing one abstract.
        """
        queries = queries or [
            "nutrition health benefits",
            "exercise physiology cardiovascular",
            "sleep quality health",
            "Mediterranean diet",
            "dietary supplements efficacy",
            "physical activity recommendations",
        ]

        all_pmids: set[str] = set()

        logger.info("Searching PubMed for %d queries...", len(queries))
        for query in queries:
            try:
                pmids = self._esearch(query, max_results=max_results_per_query)
                all_pmids.update(pmids)
            except Exception as e:
                logger.warning("Failed to search for '%s': %s", query, e)

        logger.info("Found %d unique PMIDs total", len(all_pmids))

        # Fetch in batches of 50 (API recommendation)
        pmid_list = list(all_pmids)
        documents: list[Document] = []

        for i in range(0, len(pmid_list), 50):
            batch = pmid_list[i : i + 50]
            logger.info("Fetching batch %d-%d/%d", i + 1, i + len(batch), len(pmid_list))

            try:
                xml_data = self._efetch(batch)
                batch_docs = self._parse_pubmed_xml(xml_data)
                documents.extend(batch_docs)
            except Exception as e:
                logger.warning("Failed to fetch batch: %s", e)

        logger.info("Loaded %d PubMed abstracts", len(documents))
        return documents

    def _parse_pubmed_xml(self, xml_data: str) -> list[Document]:
        """Parse PubMed XML response into Document objects.

        Args:
            xml_data: XML string from efetch.

        Returns:
            List of Documents.
        """
        root = ET.fromstring(xml_data)
        documents: list[Document] = []

        for article in root.findall(".//PubmedArticle"):
            try:
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else "unknown"

                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else "No title"

                abstract_elem = article.find(".//AbstractText")
                abstract = abstract_elem.text if abstract_elem is not None else ""

                # Publication year
                year_elem = article.find(".//PubDate/Year")
                year = year_elem.text if year_elem is not None else "N/A"

                # Journal
                journal_elem = article.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else "N/A"

                if not abstract:
                    continue  # Skip articles without abstracts

                # Format document text
                page_content = f"Title: {title}\n\nAbstract: {abstract}"

                metadata = {
                    "source": "pubmed",
                    "pmid": pmid,
                    "title": title,
                    "year": year,
                    "journal": journal,
                }

                documents.append(Document(page_content=page_content, metadata=metadata))

            except Exception as e:
                logger.warning("Failed to parse article: %s", e)

        return documents
