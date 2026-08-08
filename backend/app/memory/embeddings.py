"""Embedding function factory, lazily imported so test collection / app
startup never pulls in sentence-transformers unless embeddings are used."""
from app.config import get_settings


def get_embedding_function():
    from chromadb.utils import embedding_functions

    settings = get_settings()
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
