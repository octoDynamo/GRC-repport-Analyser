"""ChromaDB vector store operations for RAG."""
import uuid
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
from sentence_transformers import SentenceTransformer

from app.config import settings

# Embedding model (multilingual, supports French)
_embedding_model: SentenceTransformer | None = None
_chroma_client = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _embedding_model


def get_chroma_client() -> chromadb.HttpClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_collection_name(analyse_id: str) -> str:
    return f"analyse_{analyse_id.replace('-', '_')}"


async def index_document_chunks(analyse_id: str, chunks: list[str]) -> int:
    """
    Embed and index text chunks into ChromaDB for a given analysis.
    Returns the number of indexed chunks.
    """
    if not chunks:
        return 0

    client = get_chroma_client()
    model = get_embedding_model()
    collection_name = get_collection_name(analyse_id)

    try:
        # Get or create collection
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # Generate embeddings
        embeddings = model.encode(chunks, show_progress_bar=False).tolist()

        # Build IDs and metadata
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"chunk_index": i, "analyse_id": analyse_id} for i in range(len(chunks))]

        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )
        logger.info(f"Indexed {len(chunks)} chunks for analyse {analyse_id}")
        return len(chunks)
    except Exception as exc:
        logger.error(f"ChromaDB indexing failed: {exc}")
        raise


async def search_similar_chunks(
    analyse_id: str, query: str, top_k: int = 5
) -> list[dict[str, Any]]:
    """
    Search for semantically similar chunks in ChromaDB.
    Returns a list of {'text': ..., 'distance': ...} dicts.
    """
    client = get_chroma_client()
    model = get_embedding_model()
    collection_name = get_collection_name(analyse_id)

    try:
        collection = client.get_collection(collection_name)
        query_embedding = model.encode([query], show_progress_bar=False).tolist()

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, collection.count()),
            include=["documents", "distances"],
        )

        chunks = []
        for doc, dist in zip(results["documents"][0], results["distances"][0]):
            chunks.append({"text": doc, "distance": dist})
        return chunks
    except Exception as exc:
        logger.error(f"ChromaDB search failed: {exc}")
        return []


async def delete_collection(analyse_id: str) -> None:
    """Delete the ChromaDB collection for an analysis."""
    client = get_chroma_client()
    collection_name = get_collection_name(analyse_id)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass  # Collection may not exist
