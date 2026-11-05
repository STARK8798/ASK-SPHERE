
from app.database.vector_store import search_documents


TEST_QUERIES = [
    {
        "query": "Free Fire player ABDO007",
        "expected_keywords": ["ABDO007"],
    },
    {
        "query": "Free Fire esports team results",
        "expected_keywords": ["team", "results"],
    },
    {
        "query": "Free Fire World Series tournament results",
        "expected_keywords": ["world series", "tournament"],
    },
    {
        "query": "Free Fire player achievements and statistics",
        "expected_keywords": ["player", "results", "statistics"],
    },
]


def evaluate_retrieval():

    total_queries = len(TEST_QUERIES)
    successful_queries = 0

    for test in TEST_QUERIES:

        query = test["query"]
        expected_keywords = test["expected_keywords"]

        results = search_documents(query, top_k=5)

        print("\n" + "=" * 60)
        print("Query:", query)

        if not results:
            print("No documents retrieved.")
            continue

        print("\nRetrieved documents:")

        for index, result in enumerate(results, start=1):

            title = result.get("title", "")
            url = result.get("url", "")
            distance = result.get("distance", 0)

            print(f"\n{index}. {title}")
            print("URL:", url)
            print("Distance:", round(distance, 4))

        retrieved_text = " ".join(
            (
                result.get("title", "")
                + " "
                + result.get("content", "")
            ).lower()
            for result in results
        )

        matches = [
            keyword
            for keyword in expected_keywords
            if keyword.lower() in retrieved_text
        ]

        if matches:
            successful_queries += 1

        print("\nExpected keywords:", expected_keywords)
        print("Matched keywords:", matches)

    print("\n" + "=" * 60)

    print(
        f"Keyword coverage: "
        f"{successful_queries}/{total_queries}"
    )


if __name__ == "__main__":
    evaluate_retrieval()
