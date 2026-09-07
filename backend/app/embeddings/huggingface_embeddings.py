from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load the HuggingFace embedding model once
    and reuse it for subsequent requests.
    """

    return SentenceTransformer(
        settings.EMBEDDING_MODEL
    )


def embed_text(text: str) -> list[float]:
    """
    Convert a single text string into an embedding vector.
    """

    if not text or not text.strip():
        raise ValueError(
            "Cannot generate embedding for empty text."
        )

    model = get_embedding_model()

    vector = model.encode(
        text,
        normalize_embeddings=True,
    )

    return vector.tolist()


def embed_texts(
    texts: list[str],
) -> list[list[float]]:
    """
    Convert multiple text strings into embedding vectors.
    """

    if not texts:
        return []

    model = get_embedding_model()

    vectors = model.encode(
        texts,
        normalize_embeddings=True,
    )

    return [
        vector.tolist()
        for vector in vectors
    ]
