
import asyncio

from app.core.config import settings
from app.rag.retriever import retrieve_context, build_context
from app.llm.answer_generator import generate_answer


async def main():
    question = "What information is available about Free Fire esports?"

    print("\n=== 1. CONFIGURATION ===")
    print("Groq API key configured:", bool(settings.groq_api_key))
    print("Groq model:", settings.groq_model)
    print("Embedding model:", settings.embedding_model)

    print("\n=== 2. CHROMADB RETRIEVAL ===")
    documents = retrieve_context(question, top_k=5)
    print("Retrieved documents:", len(documents))

    for i, doc in enumerate(documents, start=1):
        print(f"\nDocument {i}")
        print("Title:", doc.get("title"))
        print("URL:", doc.get("url"))
        print("Distance:", doc.get("distance"))
        print("Content preview:", doc.get("content", "")[:500])

    print("\n=== 3. BUILT RAG CONTEXT ===")
    context = build_context(documents)
    print(context[:4000])

    print("\n=== 4. GROQ ANSWER GENERATION ===")
    try:
        answer = await generate_answer(
            question=question,
            context=context,
        )
        print("Generated answer:\n", answer)
    except Exception as exc:
        print("Groq generation failed:", type(exc).__name__, str(exc))


if __name__ == "__main__":
    asyncio.run(main())
