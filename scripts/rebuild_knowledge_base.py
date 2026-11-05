
from app.scrapers.web_scraper import scrape_many
from app.database.vector_store import ingest_documents, get_collection



URLS = [
    # Official Free Fire announcements
    "https://ff.garena.com/en/news",
    "https://ff.garena.com/en/article/1605/",

    # Regional Free Fire esports
    "https://esports.ff.garena.co.id/",

    # Esports World Cup
    "https://esportsworldcup.com/",
]



def main():
    print("Scraping Free Fire esports sources...")
    documents = scrape_many(URLS)

    if not documents:
        print("No pages scraped. Existing database was not changed.")
        return

    collection = get_collection()
    existing = collection.get(
        limit=max(collection.count(), 1),
        include=["metadatas"],
    )

    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        print(f"Removed {len(existing['ids'])} old records.")

    count = ingest_documents(documents)

    print(f"Pages scraped: {len(documents)}")
    print(f"Chunks ingested: {count}")
    print(f"Total ChromaDB records: {collection.count()}")


if __name__ == "__main__":
    main()
