import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

API_URL = "https://liquipedia.net/freefire/api.php"

USER_AGENT = (
    "AskSphere/1.0 "
    "(Free Fire esports research assistant; "
    "contact: sahutimu@gmail.com)"
)

# Follow Liquipedia's permitted API request rate.
REQUEST_INTERVAL = 2.2

# Number of page titles requested per API call.
BATCH_SIZE = 20

DATA_DIR = Path("data/liquipedia")
PAGES_DIR = DATA_DIR / "pages"

MASTER_TXT_FILE = DATA_DIR / "freefire_all_pages.txt"
CHECKPOINT_FILE = DATA_DIR / "checkpoint.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LiquipediaScraper:

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        PAGES_DIR.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        })

        self.last_request_time = 0.0

    # --------------------------------------------------
    # API REQUEST
    # --------------------------------------------------

    def _request(self, params):

        elapsed = time.monotonic() - self.last_request_time

        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)

        self.last_request_time = time.monotonic()

        response = self.session.get(
            API_URL,
            params=params,
            timeout=60,
        )

        if response.status_code == 429:
            logger.error(
                "Liquipedia returned HTTP 429. "
                "Stopping immediately. Do not retry "
                "until access is restored."
            )

            raise RuntimeError(
                "Liquipedia rate limit reached. "
                "Crawler stopped."
            )

        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise RuntimeError(
                f"Liquipedia API error: {data['error']}"
            )

        return data

    # --------------------------------------------------
    # CHECKPOINT
    # --------------------------------------------------

    def _load_checkpoint(self):

        if not CHECKPOINT_FILE.exists():
            return None

        try:
            with CHECKPOINT_FILE.open(
                "r",
                encoding="utf-8",
            ) as file:
                checkpoint = json.load(file)

            return checkpoint.get("apcontinue")

        except (json.JSONDecodeError, OSError):
            logger.warning(
                "Checkpoint could not be read. "
                "Starting from the beginning."
            )

            return None

    def _save_checkpoint(self, continuation):

        checkpoint = {
            "apcontinue": continuation,
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        with CHECKPOINT_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                checkpoint,
                file,
                ensure_ascii=False,
                indent=2,
            )

    # --------------------------------------------------
    # DISCOVER ALL WIKI PAGES
    # --------------------------------------------------

    def _get_page_titles(self, continuation=None):

        params = {
            "action": "query",
            "list": "allpages",
            "apnamespace": 0,
            "aplimit": BATCH_SIZE,
            "format": "json",
        }

        if continuation:
            params["apcontinue"] = continuation

        data = self._request(params)

        pages = data.get(
            "query", {}
        ).get("allpages", [])

        titles = [
            page["title"]
            for page in pages
            if page.get("title")
        ]

        next_continuation = data.get(
            "continue", {}
        ).get("apcontinue")

        return titles, next_continuation

    # --------------------------------------------------
    # FETCH PLAINTEXT EXTRACTS
    # --------------------------------------------------

    def _get_page_contents(self, titles):

        if not titles:
            return []

        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": 1,
            "exsectionformat": "plain",
            "titles": "|".join(titles),
            "format": "json",
        }

        data = self._request(params)

        pages = data.get(
            "query", {}
        ).get("pages", {})

        documents = []

        for page in pages.values():

            title = page.get("title", "Untitled")
            content = page.get("extract", "").strip()

            if not content:
                logger.warning(
                    "No plaintext extract available: %s",
                    title,
                )
                continue

            url = page.get("fullurl")

            if not url:
                url = (
                    "https://liquipedia.net/freefire/"
                    + quote(title.replace(" ", "_"), safe="/")
                )

            documents.append({
                "title": title,
                "url": url,
                "content": content,
                "source_type": "liquipedia",
                "source": "Liquipedia",
                "scraped_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            })

        return documents

    # --------------------------------------------------
    # CREATE SAFE FILE NAME
    # --------------------------------------------------

    @staticmethod
    def _file_name(title):

        safe_title = "".join(
            character
            if character.isalnum() or character in "-_"
            else "_"
            for character in title
        )

        title_hash = hashlib.sha1(
            title.encode("utf-8")
        ).hexdigest()[:10]

        return f"{safe_title[:100]}_{title_hash}.txt"

    # --------------------------------------------------
    # SAVE EACH PAGE AS TXT
    # --------------------------------------------------

    def _save_page(self, document):

        title = document["title"]
        url = document["url"]
        content = document["content"]

        file_path = (
            PAGES_DIR / self._file_name(title)
        )

        page_text = (
            f"TITLE: {title}\n"
            f"URL: {url}\n"
            f"SOURCE_TYPE: liquipedia\n"
            f"SCRAPED_AT: {document['scraped_at']}\n"
            f"\n"
            f"CONTENT:\n"
            f"{content}\n"
        )

        with file_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            file.write(page_text)

        return file_path

    # --------------------------------------------------
    # BUILD ONE COMBINED TXT FILE
    # --------------------------------------------------

    def _build_master_txt(self):

        logger.info(
            "Building combined Free Fire knowledge file..."
        )

        page_files = sorted(
            PAGES_DIR.glob("*.txt")
        )

        with MASTER_TXT_FILE.open(
            "w",
            encoding="utf-8",
        ) as master:

            master.write(
                "ASK SPHERE - LIQUIPEDIA FREE FIRE KNOWLEDGE BASE\n"
            )

            master.write(
                f"Generated: "
                f"{datetime.now(timezone.utc).isoformat()}\n"
            )

            master.write(
                f"Total pages: {len(page_files)}\n"
            )

            master.write("\n" + "=" * 80 + "\n")

            for page_file in page_files:

                master.write(
                    page_file.read_text(
                        encoding="utf-8"
                    )
                )

                master.write(
                    "\n\n" + "=" * 80 + "\n\n"
                )

        logger.info(
            "Combined TXT saved: %s",
            MASTER_TXT_FILE,
        )

    # --------------------------------------------------
    # CRAWL ALL PAGES
    # --------------------------------------------------

    def crawl_all_pages(self):

        continuation = self._load_checkpoint()

        total_saved = 0

        logger.info(
            "Starting Liquipedia Free Fire API crawl..."
        )

        try:

            while True:

                titles, next_continuation = (
                    self._get_page_titles(
                        continuation
                    )
                )

                if not titles:

                    logger.info(
                        "No more page titles found."
                    )

                    break

                logger.info(
                    "Discovered %s page titles.",
                    len(titles),
                )

                documents = self._get_page_contents(
                    titles
                )

                for document in documents:

                    self._save_page(document)

                    total_saved += 1

                continuation = next_continuation

                self._save_checkpoint(
                    continuation
                )

                logger.info(
                    "Saved %s pages in this batch. "
                    "Total this run: %s",
                    len(documents),
                    total_saved,
                )

                if not continuation:

                    logger.info(
                        "All available page titles processed."
                    )

                    break

        except Exception:

            logger.exception(
                "Crawl stopped. Checkpoint preserved."
            )

            raise

        finally:

            self._build_master_txt()

        logger.info(
            "Pages saved this run: %s",
            total_saved,
        )

        return total_saved


def scrape_liquipedia_free_fire():

    scraper = LiquipediaScraper()

    return scraper.crawl_all_pages()


if __name__ == "__main__":

    scrape_liquipedia_free_fire()