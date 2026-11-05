
from app.database.vector_store import search_documents


queries = [
    "Free Fire esports tournament teams and standings",
    "Free Fire official game update patch notes",
    "AFLATOON Free Fire player statistics",
]

for query in queries:

    print("\n" + "=" * 60)
    print("QUERY:", query)

    results = search_documents(
        query=query,
        top_k=6,
    )

    for index, document in enumerate(results, start=1):

        print(f"\nResult {index}")
        print("Title:", document["title"])
        print("Source:", document["source_type"])
        print("Distance:", document["distance"])
        print("URL:", document["url"])
