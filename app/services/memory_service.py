"""
Memory Service — ChromaDB-backed RAG for persistent conversational memory.

Stores embeddings of every user interaction and retrieves relevant past
context to inject into the AI system prompt.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

# --------------------------------------------------------------------------- #
#  ChromaDB initialisation (singleton)
# --------------------------------------------------------------------------- #

_chroma_client = None
_collection = None

COLLECTION_NAME = "senior_companion_memories"


def _get_collection():
    """Lazily initialise ChromaDB and return the memories collection."""
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


# --------------------------------------------------------------------------- #
#  Public API
# --------------------------------------------------------------------------- #

def store_interaction(user_id: int, chat_id: int, message: str, response: str) -> None:
    """
    Embed a user ↔ AI exchange into ChromaDB.

    Each exchange is stored as a single document whose text is the
    concatenation of the user message and the AI reply.  Metadata includes
    the ``user_id`` and ``chat_id`` so we can filter per-user and honour
    soft-deletes later.
    """
    collection = _get_collection()
    doc_id = f"user_{user_id}_chat_{chat_id}"
    document = f"User said: {message}\nAI replied: {response}"

    collection.upsert(
        ids=[doc_id],
        documents=[document],
        metadatas=[{
            "user_id": str(user_id),
            "chat_id": str(chat_id),
        }],
    )


def search_relevant_memories(user_id: int, query: str, n_results: int = 5) -> list[str]:
    """
    Return the *n* most relevant past interactions for this user.

    ChromaDB's built-in embedding model converts the query to a vector and
    performs cosine similarity search.  We filter by ``user_id`` so users
    can never see each other's data.
    """
    collection = _get_collection()

    # Guard: if the collection is empty, skip the query
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"user_id": str(user_id)},
    )

    documents = results.get("documents", [[]])[0]
    return documents


def soft_delete_memories(user_id: int, chat_ids: list[int]) -> None:
    """
    Remove embeddings from ChromaDB for the given chat IDs.

    Called when a user or admin soft-deletes chat records so that the AI
    can no longer retrieve those memories.
    """
    collection = _get_collection()
    ids_to_delete = [f"user_{user_id}_chat_{cid}" for cid in chat_ids]

    # ChromaDB silently ignores IDs that don't exist
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
