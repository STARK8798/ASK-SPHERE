
import hmac
import os

from dotenv import load_dotenv
from fastapi import APIRouter, Header, HTTPException

from app.services.source_discovery import discover_and_ingest

load_dotenv()

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/knowledge/discover")
async def discover_knowledge(
    x_admin_token: str = Header(default=""),
):
    expected_token = os.getenv("ASK_SPHERE_ADMIN_TOKEN", "")

    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail="Admin API is not configured.",
        )

    if not hmac.compare_digest(x_admin_token, expected_token):
        raise HTTPException(
            status_code=401,
            detail="Invalid admin token.",
        )

    try:
        return discover_and_ingest()
    except Exception as exc:
        print(f"Source discovery error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Source discovery failed. Check the server logs.",
        ) from exc
