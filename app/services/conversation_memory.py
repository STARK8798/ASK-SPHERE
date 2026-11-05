
from datetime import datetime, timezone
from functools import lru_cache

from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.core.config import settings


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    return MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=15000,
        connectTimeoutMS=15000,
        socketTimeoutMS=15000,
        tls=True,
    )


def get_messages_collection() -> Collection:
    """Get the conversation collection and create its index."""
    database = get_mongo_client()[settings.mongodb_database]
    collection = database["conversation_messages"]

    collection.create_index(
        [
            ("conversation_id", 1),
            ("created_at", DESCENDING),
        ]
    )

    return collection


def check_mongodb_connection() -> bool:
    """Check whether MongoDB is reachable."""
    try:
        get_mongo_client().admin.command("ping")
        return True
    except PyMongoError as exc:
        print(f"MongoDB connection failed: {type(exc).__name__}: {exc}")
        return False


def save_message(
    conversation_id: str,
    role: str,
    content: str,
) -> dict:
    """Save a user or assistant message."""
    if not conversation_id or not conversation_id.strip():
        raise ValueError("conversation_id cannot be empty.")

    if role not in {"user", "assistant"}:
        raise ValueError("Role must be 'user' or 'assistant'.")

    if not content or not content.strip():
        raise ValueError("Message content cannot be empty.")

    document = {
        "conversation_id": conversation_id.strip(),
        "role": role,
        "content": content.strip(),
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = get_messages_collection().insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document
    except PyMongoError as exc:
        print(f"Failed to save conversation message: {exc}")
        raise RuntimeError(
            "Could not save the conversation message to MongoDB."
        ) from exc


def get_recent_messages(
    conversation_id: str,
    limit: int = 10,
) -> list[dict]:
    """Return recent messages in chronological order."""
    if not conversation_id or not conversation_id.strip():
        return []

    limit = max(1, min(limit, 20))

    try:
        cursor = (
            get_messages_collection()
            .find(
                {"conversation_id": conversation_id.strip()},
                {
                    "_id": 0,
                    "role": 1,
                    "content": 1,
                    "created_at": 1,
                },
            )
            .sort(
                [
                    ("created_at", DESCENDING),
                    ("_id", DESCENDING),
                ]
            )
            .limit(limit)
        )

        messages = list(cursor)
        messages.reverse()

        return [
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in messages
        ]

    except PyMongoError as exc:
        print(f"Failed to load conversation history: {exc}")
        raise RuntimeError(
            "Could not load conversation history from MongoDB."
        ) from exc


def delete_conversation(conversation_id: str) -> int:
    """Delete all messages associated with a conversation."""
    if not conversation_id or not conversation_id.strip():
        return 0

    try:
        result = get_messages_collection().delete_many(
            {"conversation_id": conversation_id.strip()}
        )
        return result.deleted_count

    except PyMongoError as exc:
        print(f"Failed to delete conversation: {exc}")
        raise RuntimeError(
            "Could not delete the conversation from MongoDB."
        ) from exc


def close_mongodb_connection() -> None:
    """Close the cached MongoDB client."""
    client = get_mongo_client()
    client.close()
    get_mongo_client.cache_clear()
