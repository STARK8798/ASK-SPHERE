
from app.services.liquipedia_scraper import (
    scrape_liquipedia_free_fire,
)

documents = scrape_liquipedia_free_fire(limit=5)

print("\nTotal documents:", len(documents))

for document in documents:
    print("\nTitle:", document["title"])
    print("URL:", document["url"])
    print("Content:", document["content"][:300])
