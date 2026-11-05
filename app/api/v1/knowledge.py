from collections import Counter

from app.database.vector_store import get_collection

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.services.knowledge_refresh import (
    refresh_knowledge_base,
    get_refresh_status,
)

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"],
)


@router.get("/refresh-status")
def refresh_status():
    return get_refresh_status()


@router.post("/refresh")
def manual_refresh(background_tasks: BackgroundTasks):
    status = get_refresh_status()

    if status["running"]:
        raise HTTPException(
            status_code=409,
            detail="Knowledge base refresh is already running.",
        )

    background_tasks.add_task(refresh_knowledge_base)

    return {
        "message": "Knowledge base refresh started.",
        "status": "running",
    }
@router.get("/stats")
def knowledge_stats():
    try:
        collection = get_collection()

        total_chunks = collection.count()

        source_counts = Counter()

        # Fetch metadata in batches to avoid loading everything at once
        batch_size = 1000

        for offset in range(0, total_chunks, batch_size):
            result = collection.get(
                limit=batch_size,
                offset=offset,
                include=["metadatas"],
            )

            metadatas = result.get("metadatas") or []

            for metadata in metadatas:
                source_type = metadata.get("source_type", "unknown")
                source_counts[source_type] += 1

        return {
            "total_chunks": total_chunks,
            "source_breakdown": dict(source_counts),
            "source_types": list(source_counts.keys()),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve knowledge statistics: {str(exc)}",
        )