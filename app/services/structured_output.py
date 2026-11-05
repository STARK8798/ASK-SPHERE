
import logging
from datetime import datetime, timezone

from app.scrapers.web_scraper import scrape_many
from app.database.vector_store import (
    ingest_documents_incrementally,
    get_collection,
)

logger = logging.getLogger(__name__)

SOURCE_URLS = [
    "https://ff.garena.com/en/news",
    "https://esports.ff.garena.co.id/",
    "https://esportsworldcup.com/",
]


def refresh_knowledge_base() -> dict:
    started_at = datetime.now(timezone.utc).isoformat()

    logger.info("Starting Ask Sphere knowledge refresh")

    documents = scrape_many(SOURCE_URLS)

    if not documents:
        logger.warning(
            "Refresh skipped: no pages scraped; existing data preserved"
        )
        return {
            "status": "no_updates",
            "started_at": started_at,
            "pages_scraped": 0,
            "chunks_updated": 0,
            "total_records": get_collection().count(),
        }

    # Record when each source was refreshed.
    for document in documents:
        document["scraped_at"] = started_at

    result = ingest_documents_incrementally(documents)
    total_records = get_collection().count()

    logger.info(
        "Refresh complete: sources=%s chunks=%s removed=%s total=%s",
        result["sources"],
        result["chunks"],
        result["removed"],
        total_records,
    )

    return {
        "status": "success",
        "started_at": started_at,
        "pages_scraped": len(documents),
        "sources_updated": result["sources"],
        "chunks_updated": result["chunks"],
        "stale_chunks_removed": result["removed"],
        "total_records": total_records,
    }
