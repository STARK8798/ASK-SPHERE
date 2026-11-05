
from fastapi import APIRouter, HTTPException

from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.chat_service import answer_question

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await answer_question(
            question=request.question,
            conversation_id=request.conversation_id,
        )
        return ChatResponse(**result)

    except Exception as exc:
        print(f"Ask Sphere error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Ask Sphere could not process your question.",
        ) from exc
