
from uuid import uuid4

from app.services.conversation_memory import (
    save_message,
    get_recent_messages,
    delete_conversation,
)


def main():
    conversation_id = f"test-{uuid4()}"

    try:
        save_message(
            conversation_id,
            "user",
            "When is the next Free Fire tournament?",
        )

        save_message(
            conversation_id,
            "assistant",
            "I will check the available esports information.",
        )

        messages = get_recent_messages(conversation_id)

        print("Retrieved messages:")
        for message in messages:
            print(f"{message['role']}: {message['content']}")

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

        print("\nConversation memory test passed!")

    finally:
        deleted = delete_conversation(conversation_id)
        print(f"Test messages deleted: {deleted}")


if __name__ == "__main__":
    main()
