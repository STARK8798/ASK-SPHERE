
from app.services.conversation_memory import (
    check_mongodb_connection,
    get_mongo_client,
)


def main():
    print("Testing MongoDB Atlas connection...")

    try:
        client = get_mongo_client()
        client.admin.command("ping")

        print("SUCCESS: MongoDB Atlas connected!")
        print("MongoDB version:", client.server_info()["version"])

    except Exception as exc:
        print("FAILED:", type(exc).__name__)
        print("Details:", exc)

    finally:
        get_mongo_client.cache_clear()


if __name__ == "__main__":
    main()
