
from app.scrapers.web_scraper import scrape_many
from app.database.vector_store import ingest_documents, get_collection

URLS = [
    "https://ff.garena.com/en/news",
    "https://esports.ff.garena.co.id/",
]


def main():
    print("Starting Free Fire esports ingestion...")

    documents = scrape_many(URLS)
    print(f"Pages successfully scraped: {len(documents)}")

    if not documents:
        print("No pages were scraped. Check the URLs and scraper output.")
        return

    count = ingest_documents(documents)
    print(f"Documents ingested: {count}")

    collection = get_collection()
    print(f"Total records in ChromaDB: {collection.count()}")


if __name__ == "__main__":
    main()
