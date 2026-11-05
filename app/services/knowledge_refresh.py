
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.liquipedia_scraper import scrape_liquipedia_free_fire
from app.services.liquipedia_ingestion import ingest_liquipedia_documents

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

refresh_status = {
    "running": False,
    "last_started": None,
    "last_completed": None,
    "last_error": None,
    "last_result": None,
}


def refresh_knowledge_base():
    """
    Crawl Liquipedia and update its documents in ChromaDB.
    """

    if refresh_status["running"]:
        logger.warning("Knowledge refresh already running.")
        return

    refresh_status["running"] = True
    refresh_status["last_started"] = datetime.now(
        timezone.utc
    ).isoformat()
    refresh_status["last_error"] = None

    try:
        logger.info("Starting Liquipedia knowledge refresh.")

        # Crawl pages and resume from existing checkpoint.
        scrape_liquipedia_free_fire()

        # Update ChromaDB incrementally.
        result = ingest_liquipedia_documents()

        refresh_status["last_result"] = result
        refresh_status["last_completed"] = datetime.now(
            timezone.utc
        ).isoformat()

        logger.info("Knowledge refresh completed: %s", result)

    except Exception as exc:
        refresh_status["last_error"] = str(exc)

        logger.exception("Knowledge refresh failed.")

    finally:
        refresh_status["running"] = False


def start_knowledge_scheduler():
    """
    Start the scheduler once when FastAPI starts.
    """

    if scheduler.running:
        return

    scheduler.add_job(
        refresh_knowledge_base,
        trigger="interval",
        hours=24,
        id="liquipedia_refresh",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    logger.info("Knowledge refresh scheduler started.")


def stop_knowledge_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


def get_refresh_status():
    return refresh_status.copy()
