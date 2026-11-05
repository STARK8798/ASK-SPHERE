
from app.database.vector_store import search_documents


MAX_DISTANCE = 0.85


def retrieve_context(
    question: str,
    top_k: int = 6,
) -> list[dict]:
    """Return relevant chunks, excluding weak matches."""
    results = search_documents(query=question, top_k=top_k)

    return [
        document
        for document in results
        if document.get("distance", 2.0) <= MAX_DISTANCE
        and document.get("content", "").strip()
    ]


def build_context(documents: list[dict]) -> str:
    if not documents:
        return (
            "NO_RELEVANT_SOURCES_FOUND. "
            "The knowledge base did not return sufficiently relevant evidence."
        )

    sections = []

    for index, document in enumerate(documents, start=1):
        title = document.get("title", "Untitled")
        url = document.get("url", "")
        chunk_index = document.get("chunk_index", -1)
        content = document.get("content", "")

        sections.append(
            f"[Source {index}]\n"
            f"Title: {title}\n"
            f"URL: {url}\n"
            f"Chunk: {chunk_index}\n"
            f"Evidence:\n{content}"
        )

    return "\n\n".join(sections)
