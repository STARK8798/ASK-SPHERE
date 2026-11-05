
from app.database.vector_store import get_collection

collection = get_collection()

results = collection.get(
    where={"source_type": "liquipedia"},
    include=["metadatas"],
    limit=5,
)

print("Liquipedia chunks found:", len(results["ids"]))

for metadata in results["metadatas"]:
    print("\nTitle:", metadata.get("title"))
    print("URL:", metadata.get("url"))
    print("Source:", metadata.get("source_type"))
