"""Chroma-backed vector store for conversation/document embeddings (section 3.4).

Swappable for FAISS later if needed — this module is the only place that
should know it's Chroma specifically; callers use add()/query()/delete().
"""
import uuid
from dataclasses import dataclass

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "oreo_memory"


@dataclass
class VectorHit:
    id: str
    text: str
    metadata: dict
    distance: float


class VectorStore:
    def __init__(self):
        self._client = None
        self._collection = None

    def _get_collection(self):
        if self._collection is None:
            import chromadb

            from app.memory.embeddings import get_embedding_function

            settings = get_settings()
            self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=get_embedding_function(),
            )
        return self._collection

    def add(self, text: str, metadata: dict, doc_id: str | None = None) -> str:
        doc_id = doc_id or str(uuid.uuid4())
        collection = self._get_collection()
        collection.add(ids=[doc_id], documents=[text], metadatas=[metadata])
        return doc_id

    def add_many(self, texts: list[str], metadatas: list[dict], ids: list[str] | None = None) -> list[str]:
        ids = ids or [str(uuid.uuid4()) for _ in texts]
        collection = self._get_collection()
        collection.add(ids=ids, documents=texts, metadatas=metadatas)
        return ids

    def query(self, text: str, n_results: int = 5, where: dict | None = None) -> list[VectorHit]:
        collection = self._get_collection()
        result = collection.query(query_texts=[text], n_results=n_results, where=where)
        hits: list[VectorHit] = []
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]
        for doc_id, doc, meta, dist in zip(ids, docs, metas, dists):
            hits.append(VectorHit(id=doc_id, text=doc, metadata=meta or {}, distance=dist))
        return hits

    def delete(self, doc_id: str) -> None:
        collection = self._get_collection()
        collection.delete(ids=[doc_id])


_default_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _default_store
    if _default_store is None:
        _default_store = VectorStore()
    return _default_store
