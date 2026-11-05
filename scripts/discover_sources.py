
import json
import logging

from app.services.source_discovery import discover_and_ingest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def main():
    try:
        result = discover_and_ingest()
        print(json.dumps(result, indent=2))
    except Exception:
        logging.exception("Source discovery failed")
        raise


if __name__ == "__main__":
    main()
