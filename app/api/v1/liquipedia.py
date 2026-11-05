
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.services.liquipedia_scraper import (
    scrape_liquipedia_free_fire,
)

from app.services.liquipedia_ingestion import (
    ingest_liquipedia_documents,
)

router = APIRouter(
    prefix="/liquipedia",
    tags=["Liquipedia Free Fire"],
)


def run_liquipedia_crawl():
    """
    Run the existing Liquipedia scraper.
    """
    scrape_liquipedia_free_fire()


def run_liquipedia_ingestion():
    """
    Ingest scraped Liquipedia JSONL documents into ChromaDB.
    """
    ingest_liquipedia_documents()


@router.post("/crawl")
def start_liquipedia_crawl(
    background_tasks: BackgroundTasks,
):
    """
    Start the Liquipedia Free Fire crawler.
    """

    background_tasks.add_task(
        run_liquipedia_crawl
    )

    return {
        "status": "started",
        "message": (
            "Liquipedia crawl started in the background. "
            "Check server logs for progress."
        ),
    }


@router.post("/ingest")
def start_liquipedia_ingestion(
    background_tasks: BackgroundTasks,
):
    """
    Start ingestion of existing Liquipedia JSONL data.
    """

    background_tasks.add_task(
        run_liquipedia_ingestion
    )

    return {
        "status": "started",
        "message": (
            "Liquipedia ingestion started in the background."
        ),
    }
