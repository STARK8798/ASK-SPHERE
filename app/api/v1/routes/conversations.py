
from fastapi import APIRouter, HTTPException

from app.services.conversation_memory import (
    get_recent_messages,
    delete_conversation,
)

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str):
    try:
        messages = get_recent_messages(
            conversation_id=conversation_id,
            limit=20,
        )

        if not messages:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )

        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "total_messages": len(messages),
        }

    except HTTPException:
        raise

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.delete("/{conversation_id}")
def remove_conversation(conversation_id: str):
    try:
        deleted_count = delete_conversation(conversation_id)

        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )

        return {
            "conversation_id": conversation_id,
            "deleted_messages": deleted_count,
            "message": "Conversation deleted successfully.",
        }

    except HTTPException:
        raise

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
