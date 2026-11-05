
from urllib.parse import urlparse

import httpx
import trafilatura


ALLOWED_DOMAINS = {
    "ff.garena.com",
    "liquipedia.net",
    "escharts.com",
    "ffesports.garena.com",
    "esports.ff.garena.com",
    "esports.ff.garena.co.id",
    "esportsworldcup.com",
}


def scrape_url(url: str) -> dict | None:
    """Download and extract text from an approved Free Fire esports URL."""
    parsed = urlparse(url)

    if parsed.scheme != "https" or not any(
        parsed.hostname == domain
        or (
            parsed.hostname is not None
            and parsed.hostname.endswith("." + domain)
        )
        for domain in ALLOWED_DOMAINS
    ):
        print(f"Skipping unapproved URL: {url}")
        return None

    
    try:
        with httpx.Client(
            timeout=20,
            follow_redirects=True,
            max_redirects=5,
            headers={"User-Agent": "AskSphere/1.0"},
        ) as client:
            response = client.get(url)

        # Validate the final destination after redirects.
        final_host = response.url.host

        if not final_host or not any(
            final_host == domain
            or final_host.endswith("." + domain)
            for domain in ALLOWED_DOMAINS
        ):
            print(f"Blocked redirect to unapproved host: {final_host}")
            return None

        response.raise_for_status()

        content = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
        )

        if not content or not content.strip():
            print(f"No readable content found: {response.url}")
            return None

        return {
            "title": str(response.url.host),
            "url": str(response.url),
            "content": content[:20000],
            "source_type": "web",
        }

    except Exception as exc:
        print(f"Scraping failed for {url}: {exc}")
        return None


def scrape_many(urls: list[str]) -> list[dict]:
    """Scrape multiple approved URLs."""
    documents = []

    for url in urls:
        print(f"Scraping: {url}")
        document = scrape_url(url)

        if document:
            documents.append(document)

    return documents
