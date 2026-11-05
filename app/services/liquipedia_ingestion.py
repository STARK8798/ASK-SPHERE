
import logging
from pathlib import Path
from datetime import datetime, timezone

from app.database.vector_store import (
    ingest_documents_incrementally,
)

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

DATA_DIR = Path("data/liquipedia")
PAGES_DIR = DATA_DIR / "pages"

BATCH_SIZE = 20

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LiquipediaIngestion:

    def __init__(self):
        if not PAGES_DIR.exists():
            raise FileNotFoundError(
                f"Liquipedia pages directory not found: {PAGES_DIR}"
            )

    # --------------------------------------------------
    # PARSE TXT PAGE
    # --------------------------------------------------

    @staticmethod
    def _parse_page(file_path: Path):

        text = file_path.read_text(encoding="utf-8")

        title = "Untitled"
        url = ""
        source_type = "liquipedia"
        scraped_at = ""

        content_lines = []
        content_started = False

        for line in text.splitlines():

            if line.startswith("TITLE: "):
                title = line[len("TITLE: "):].strip()

            elif line.startswith("URL: "):
                url = line[len("URL: "):].strip()

            elif line.startswith("SOURCE_TYPE: "):
                source_type = line[len("SOURCE_TYPE: "):].strip()

            elif line.startswith("SCRAPED_AT: "):
                scraped_at = line[len("SCRAPED_AT: "):].strip()

            elif line.strip() == "CONTENT:":
                content_started = True

            elif content_started:
                content_lines.append(line)

        content = "\n".join(content_lines).strip()

        if not content:
            logger.warning(
                "Skipping empty page: %s",
                file_path.name,
            )
            return None

        if not url:
            logger.warning(
                "Missing URL in page: %s",
                file_path.name,
            )
            return None

        if not scraped_at:
            scraped_at = datetime.now(
                timezone.utc
            ).isoformat()

        return {
            "title": title,
            "url": url,
            "content": content,
            "source_type": source_type,
            "scraped_at": scraped_at,
        }

    # --------------------------------------------------
    # LOAD TXT FILES
    # --------------------------------------------------

    def load_documents(self):

        documents = []

        files = sorted(PAGES_DIR.glob("*.txt"))

        logger.info(
            "Found %s Liquipedia TXT files.",
            len(files),
        )

        for file_path in files:

            try:
                document = self._parse_page(file_path)

                if document:
                    documents.append(document)

            except Exception:
                logger.exception(
                    "Failed to read %s",
                    file_path.name,
                )

        logger.info(
            "Successfully parsed %s documents.",
            len(documents),
        )

        return documents

    # --------------------------------------------------
    # INGEST INTO CHROMADB
    # --------------------------------------------------

    def ingest_all_pages(self):

        documents = self.load_documents()

        if not documents:

            logger.warning(
                "No documents available for ingestion."
            )

            return {
                "sources": 0,
                "chunks": 0,
                "removed": 0,
            }

        totals = {
            "sources": 0,
            "chunks": 0,
            "removed": 0,
        }

        total_documents = len(documents)

        for start in range(
            0,
            total_documents,
            BATCH_SIZE,
        ):

            batch = documents[
                start:start + BATCH_SIZE
            ]

            result = ingest_documents_incrementally(
                batch
            )

            if not isinstance(result, dict):
                logger.warning(
                    "Unexpected ingestion result: %s",
                    result,
                )
                continue

            for key in totals:
                totals[key] += result.get(key, 0)

            processed = min(
                start + len(batch),
                total_documents,
            )

            logger.info(
                "Ingestion progress: %s/%s documents",
                processed,
                total_documents,
            )

        logger.info(
            "Liquipedia ingestion completed: %s",
            totals,
        )

        return totals


# --------------------------------------------------
# API COMPATIBILITY FUNCTION
# --------------------------------------------------

def ingest_liquipedia_documents():
    """
    Function imported by app.api.v1.liquipedia.
    """
    ingestion = LiquipediaIngestion()
    return ingestion.ingest_all_pages()


# --------------------------------------------------
# BACKWARD COMPATIBILITY
# --------------------------------------------------

def ingest_liquipedia_free_fire():
    """
    Existing function name retained for compatibility.
    """
    return ingest_liquipedia_documents()


# --------------------------------------------------
# DIRECT EXECUTION
# --------------------------------------------------

if __name__ == "__main__":

    result = ingest_liquipedia_documents()

    print("\nLiquipedia ingestion result:")
    print(result)
