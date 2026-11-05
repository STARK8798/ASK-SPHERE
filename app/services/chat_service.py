
from uuid import uuid4

from app.llm.answer_validator import validate_answer
from app.services.query_rewriter import rewrite_query
from app.rag.retriever import retrieve_context, build_context
from app.llm.answer_generator import generate_answer
from app.services.conversation_memory import (
    save_message,
    get_recent_messages,
)


def calculate_confidence(documents: list[dict]) -> str:
    """
    Estimate confidence based on retrieved evidence quality.

    This measures retrieval quality, not factual correctness.
    """

    if not documents:
        return "low"

    distances = [
        document.get("distance")
        for document in documents
        if isinstance(document.get("distance"), (int, float))
    ]

    if not distances:
        return "medium"

    average_distance = sum(distances) / len(distances)

    if len(documents) >= 3 and average_distance <= 0.50:
        return "high"

    if average_distance <= 0.70:
        return "medium"

    return "low"


async def answer_question(
    question: str,
    conversation_id: str | None = None,
) -> dict:

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    conversation_id = (
        conversation_id.strip()
        if conversation_id and conversation_id.strip()
        else str(uuid4())
    )

    # Load conversation history before saving the current question.
    history = get_recent_messages(
        conversation_id=conversation_id,
        limit=10,
    )

    # Rewrite follow-up questions into standalone search queries.
    retrieval_query = await rewrite_query(
        question=question,
        history=history,
    )

    print("Original question:", question)
    print("Rewritten query:", retrieval_query)

    # Retrieve relevant knowledge base documents.
    documents = retrieve_context(
        retrieval_query,
        top_k=6,
    )

    print("Retrieved documents:", len(documents))

    context = build_context(documents)

    # Generate the answer using the original question and history.
    answer = await generate_answer(
        question=question,
        context=context,
        history=history,
    )

    # Validate the generated answer against retrieved evidence.
    validation = await validate_answer(
        question=question,
        answer=answer,
        context=context,
    )

    print("Answer validation:", validation)

    # Save the current conversation messages.
    save_message(
        conversation_id=conversation_id,
        role="user",
        content=question,
    )

    save_message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
    )

    # Collect unique source URLs.
    sources = []
    seen_urls = set()

    for document in documents:
        url = document.get("url", "").strip()

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)

        sources.append({
            "title": document.get("title") or "Untitled",
            "url": url,
        })

    # Estimate confidence from retrieval quality.
    confidence = calculate_confidence(documents)

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
        "validation": validation,
        "conversation_id": conversation_id,
    }
