
import logging
import json

from app.services.knowledge_refresh import refresh_knowledge_base


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "knowledge_refresh.log",
            encoding="utf-8",
        ),
    ],
)


def main():
    result = refresh_knowledge_base()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
