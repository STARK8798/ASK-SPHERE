
from functools import lru_cache

from groq import AsyncGroq

from app.core.config import settings


REWRITE_PROMPT = """
You rewrite follow-up questions into standalone search queries.

Rules:
1. Use the conversation history to understand the current topic.
2. Resolve references such as "it", "that", "they", and "tell me more".
3. Preserve the user's actual intent.
4. Do not answer the question.
5. Return only the rewritten search query.
6. If the question is already clear, return it unchanged.
7. Do not invent details that are not in the conversation.
"""


@lru_cache(maxsize=1)
def get_groq_client() -> AsyncGroq:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    return AsyncGroq(api_key=settings.groq_api_key)


async def rewrite_query(
    question: str,
    history: list[dict] | None = None,
) -> str:
    if not history:
        return question

    messages = [
        {
            "role": "system",
            "content": REWRITE_PROMPT,
        }
    ]

    for item in history[-6:]:
        role = item.get("role")
        content = item.get("content")

        if (
            role in {"user", "assistant"}
            and isinstance(content, str)
            and content.strip()
        ):
            messages.append({
                "role": role,
                "content": content[:2000],
            })

    messages.append({
        "role": "user",
        "content": (
            "Rewrite this question for information retrieval:\n"
            f"{question}"
        ),
    })

    try:
        response = await get_groq_client().chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=0,
            max_tokens=150,
        )

        rewritten = response.choices[0].message.content

        if rewritten and rewritten.strip():
            return rewritten.strip()

    except Exception as exc:
        print(
            f"Query rewriting failed: {type(exc).__name__}: {exc}"
        )

    # Fall back to the original question if rewriting fails.
    return question
