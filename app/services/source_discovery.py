
import logging
import os
from urllib.parse import urlparse, urldefrag

import httpx
from dotenv import load_dotenv

from app.scrapers.web_scraper import scrape_many
from app.database.vector_store import (
    get_collection,
    ingest_documents_incrementally,
)

load_dotenv()
logger = logging.getLogger(__name__)

ALLOWED_DOMAINS = {
    "ff.garena.com",
    "liquipedia.net",
    "escharts.com",
    "ffesports.garena.com",
    "esports.ff.garena.com",
    "esports.ff.garena.co.id",
    "esportsworldcup.com",
}

SEARCH_QUERIES = [
    "Garena Free Fire esports tournament official",
    "Free Fire esports tournament results official",
    "Free Fire esports championship news",
]

MAX_CANDIDATES = 15


def is_approved_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        return (
            parsed.scheme == "https"
            and parsed.username is None
            and parsed.password is None
            and any(
                host == domain or host.endswith("." + domain)
                for domain in ALLOWED_DOMAINS
            )
        )
    except (ValueError, TypeError):
        return False


def discover_urls() -> list[str]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is missing. Add it to your .env file."
        )

    candidates = []
    seen = set()

    with httpx.Client(timeout=30.0) as client:
        for query in SEARCH_QUERIES:
            response = client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 8,
                },
            )
            response.raise_for_status()
            payload = response.json()

            for result in payload.get("results", []):
                raw_url = result.get("url", "")
                if not raw_url or not is_approved_url(raw_url):
                    continue

                normalized_url, _ = urldefrag(raw_url)
                if normalized_url not in seen:
                    seen.add(normalized_url)
                    candidates.append(normalized_url)

                if len(candidates) >= MAX_CANDIDATES:
                    return candidates

    return candidates


def discover_and_ingest() -> dict:
    logger.info("Starting source discovery")

    urls = discover_urls()
    logger.info("Approved candidate URLs: %s", len(urls))

    if not urls:
        return {
            "status": "no_candidates",
            "candidates_found": 0,
            "pages_scraped": 0,
            "chunks_updated": 0,
            "total_records": get_collection().count(),
            "urls": [],
        }

    documents = scrape_many(urls)

    if not documents:
        return {
            "status": "no_pages_scraped",
            "candidates_found": len(urls),
            "pages_scraped": 0,
            "chunks_updated": 0,
            "total_records": get_collection().count(),
            "urls": urls,
        }

    result = ingest_documents_incrementally(documents)

    return {
        "status": "success",
        "candidates_found": len(urls),
        "pages_scraped": len(documents),
        "sources_updated": result["sources"],
        "chunks_updated": result["chunks"],
        "stale_chunks_removed": result["removed"],
        "total_records": get_collection().count(),
        "urls": [document["url"] for document in documents],
    }
