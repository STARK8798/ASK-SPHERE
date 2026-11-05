
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer
from app.services.search_cache import search_cache
from app.core.config import settings


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


# --------------------------------------------------
# EMBEDDING MODEL
# --------------------------------------------------

@lru_cache
def get_embedding_model():
    return SentenceTransformer(settings.embedding_model)


# --------------------------------------------------
# CHROMADB COLLECTION
# --------------------------------------------------

@lru_cache
def get_collection():
    Path(settings.chroma_path).mkdir(
        parents=True,
        exist_ok=True,
    )

    client = chromadb.PersistentClient(
        path=settings.chroma_path
    )

    return client.get_or_create_collection(
        name="freefire_esports",
        metadata={"hnsw:space": "cosine"},
    )


# --------------------------------------------------
# TEXT CHUNKING
# --------------------------------------------------

def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:

    text = " ".join(text.split())

    if not text:
        return []

    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk size or overlap.")

    chunks = []
    start = 0

    while start < len(text):

        end = min(start + chunk_size, len(text))

        if end < len(text):

            boundary = text.rfind(" ", start, end)

            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    return chunks


# --------------------------------------------------
# ENHANCED DOCUMENT TEXT
# --------------------------------------------------

def prepare_document_text(
    title: str,
    source_type: str,
    chunk: str,
) -> str:

    return (
        f"Page title: {title}\n"
        f"Source type: {source_type}\n"
        f"Content: {chunk}"
    )


# --------------------------------------------------
# DOCUMENT INGESTION
# --------------------------------------------------

def ingest_documents(
    documents: list[dict[str, Any]],
) -> int:

    collection = get_collection()
    model = get_embedding_model()

    ids = []
    texts = []
    metadatas = []

    for document in documents:

        content = document.get("content", "").strip()
        url = document.get("url", "")
        title = document.get("title", "Untitled")
        source_type = document.get("source_type", "web")
        scraped_at = document.get("scraped_at", "")

        if not content:
            continue

        chunks = chunk_text(content)

        for chunk_index, chunk in enumerate(chunks):

            raw_id = f"{url}::{chunk_index}"

            chunk_id = sha256(
                raw_id.encode("utf-8")
            ).hexdigest()

            enhanced_text = prepare_document_text(
                str(title),
                str(source_type),
                chunk,
            )

            ids.append(chunk_id)
            texts.append(enhanced_text)

            metadatas.append({
                "title": str(title),
                "url": str(url),
                "source_type": str(source_type),
                "scraped_at": str(scraped_at),
                "chunk_index": chunk_index,
            })

    if not ids:
        return 0

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
    ).tolist()

    batch_size = 100

    for start in range(0, len(ids), batch_size):

        end = start + batch_size

        collection.upsert(
            ids=ids[start:end],
            documents=texts[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )
    search_cache.clear()
    return len(ids)


# --------------------------------------------------
# INCREMENTAL INGESTION
# --------------------------------------------------

def ingest_documents_incrementally(
    documents: list[dict[str, Any]],
) -> dict[str, int]:

    collection = get_collection()
    model = get_embedding_model()

    totals = {
        "sources": 0,
        "chunks": 0,
        "removed": 0,
    }

    for document in documents:

        url = document.get("url", "").strip()
        content = document.get("content", "").strip()

        if not url or not content:
            continue

        chunks = chunk_text(content)

        if not chunks:
            continue

        existing = collection.get(
            where={"url": url},
            include=["metadatas"],
        )

        old_ids = existing.get("ids", [])

        ids = []
        metadatas = []
        enhanced_chunks = []

        title = str(
            document.get("title", "Untitled")
        )

        source_type = str(
            document.get("source_type", "web")
        )

        scraped_at = str(
            document.get("scraped_at", "")
        )

        for index, chunk in enumerate(chunks):

            raw_id = f"{url}::{index}"

            chunk_id = sha256(
                raw_id.encode("utf-8")
            ).hexdigest()

            ids.append(chunk_id)

            enhanced_text = prepare_document_text(
                title,
                source_type,
                chunk,
            )

            enhanced_chunks.append(enhanced_text)

            metadatas.append({
                "title": title,
                "url": url,
                "source_type": source_type,
                "scraped_at": scraped_at,
                "chunk_index": index,
            })

        embeddings = model.encode(
            enhanced_chunks,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        ).tolist()

        collection.upsert(
            ids=ids,
            documents=enhanced_chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        stale_ids = [
            old_id
            for old_id in old_ids
            if old_id not in ids
        ]

        if stale_ids:
            collection.delete(ids=stale_ids)

        totals["sources"] += 1
        totals["chunks"] += len(chunks)
        totals["removed"] += len(stale_ids)
    
    search_cache.clear()
    return totals


# --------------------------------------------------
# QUERY TYPE DETECTION
# --------------------------------------------------

def detect_preferred_sources(
    query: str,
) -> list[str]:

    query = query.lower()

    official_keywords = [
        "official announcement",
        "patch notes",
        "game update",
        "new update",
        "release",
        "maintenance",
        "new character",
        "new weapon",
        "new event",
        "official news",
        "garena announcement",
    ]

    esports_keywords = [
        "player",
        "players",
        "team",
        "teams",
        "tournament",
        "tournaments",
        "transfer",
        "transfers",
        "roster",
        "esports",
        "championship",
        "champion",
        "results",
        "standings",
        "ranking",
        "rankings",
        "stats",
        "statistics",
        "achievements",
        "career",
        "match",
        "matches",
        "world series",
        "league",
    ]

    if any(
        keyword in query
        for keyword in official_keywords
    ):
        return ["web"]

    if any(
        keyword in query
        for keyword in esports_keywords
    ):
        return ["liquipedia"]

    return []


# --------------------------------------------------
# SEARCH DOCUMENTS
# --------------------------------------------------


def search_documents(
    query: str,
    top_k: int = 6,
) -> list[dict[str, Any]]:

    if not query.strip() or top_k < 1:
        return []

    # Normalize the cache key.
    cache_key = (
        f"{query.strip().lower()}::{top_k}"
    )

    # Return cached results if available.
    cached_results = search_cache.get(cache_key)

    if cached_results is not None:
        return cached_results

    collection = get_collection()

    count = collection.count()

    if count == 0:
        return []

    model = get_embedding_model()

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    preferred_sources = detect_preferred_sources(
        query
    )

    documents = {}

    def process_results(
        results,
        source_boost=0.0,
    ):

        result_documents = results.get(
            "documents", [[]]
        )[0]

        result_metadatas = results.get(
            "metadatas", [[]]
        )[0]

        result_distances = results.get(
            "distances", [[]]
        )[0]

        for index, content in enumerate(
            result_documents
        ):

            metadata = (
                result_metadatas[index] or {}
            )

            distance = float(
                result_distances[index]
            )

            url = metadata.get("url", "")

            chunk_index = metadata.get(
                "chunk_index", -1
            )

            source_type = metadata.get(
                "source_type", "web"
            )

            document_key = (
                f"{url}::{chunk_index}"
                if url
                else f"{source_type}::{content[:100]}"
            )

            adjusted_distance = (
                distance - source_boost
            )

            document = {
                "content": content,
                "title": metadata.get(
                    "title", "Untitled"
                ),
                "url": url,
                "source_type": source_type,
                "scraped_at": metadata.get(
                    "scraped_at", ""
                ),
                "chunk_index": chunk_index,
                "distance": distance,
                "adjusted_distance": adjusted_distance,
            }

            existing = documents.get(
                document_key
            )

            if (
                existing is None
                or adjusted_distance
                < existing["adjusted_distance"]
            ):

                documents[document_key] = document

    # Global retrieval.
    global_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k * 3, count),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    process_results(global_results)

    # Source-specific retrieval.
    for source in preferred_sources:

        try:

            source_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k * 2, count),
                where={
                    "source_type": source
                },
                include=[
                    "documents",
                    "metadatas",
                    "distances",
                ],
            )

            process_results(
                source_results,
                source_boost=0.05,
            )

        except Exception as exc:

            print(
                f"Source-specific retrieval failed "
                f"for {source}: {exc}"
            )

    ranked_documents = sorted(
        documents.values(),
        key=lambda document: (
            document["adjusted_distance"]
        ),
    )

    final_documents = ranked_documents[:top_k]

    for document in final_documents:

        document.pop(
            "adjusted_distance",
            None,
        )

    # Cache the final search results.
    search_cache.set(
        cache_key,
        final_documents,
    )

    return final_documents
