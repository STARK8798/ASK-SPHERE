
from app.scrapers.web_scraper import scrape_many
from app.database.vector_store import (
    ingest_documents_incrementally,
    get_collection,
)

URLS = [
    "https://ff.garena.com/en/news",
    "https://esports.ff.garena.co.id/",
    "https://esportsworldcup.com/",
]


def main():
    print("Starting incremental Ask Sphere knowledge-base update...")

    documents = scrape_many(URLS)
    print(f"Successfully scraped pages: {len(documents)}")

    if not documents:
        print("No pages were scraped. Existing knowledge base is unchanged.")
        return

    result = ingest_documents_incrementally(documents)

    print(f"Sources updated: {result['sources']}")
    print(f"Chunks added or updated: {result['chunks']}")
    print(f"Stale chunks removed: {result['removed']}")
    print(f"Total ChromaDB records: {get_collection().count()}")


if __name__ == "__main__":
    main()
