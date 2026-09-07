from app.embeddings.huggingface_embeddings import (
    embed_text,
)
from app.vectorstore.qdrant_client import (
    QdrantVectorStore,
)
from app.vectorstore.retriever import (
    InvestigationRetriever,
)


def test_semantic_investigation_retrieval():

    vector_store = QdrantVectorStore()

    vector_store.ensure_collection()

    vector = embed_text(
        "Payment API database connection failure"
    )

    vector_store.upsert(
        investigation_id=124,
        vector=vector,
        payload={
            "investigation_id": 124,
            "user_id": 1,
            "summary": (
                "Payment API experienced "
                "database connection failures."
            ),
            "root_cause": (
                "Database connection pool exhaustion"
            ),
            "failed_component": "payment-api",
            "severity": "HIGH",
            "confidence": 0.91,
        },
    )

    retriever = InvestigationRetriever(
        vector_store=vector_store,
    )

    results = retriever.search(
        "Payment service database timeout",
        limit=5,
    )

    assert len(results) == 1

    result = results[0]

    assert result["investigation_id"] == 124

    assert (
        result["root_cause"]
        == "Database connection pool exhaustion"
    )

    assert (
        result["failed_component"]
        == "payment-api"
    )

    assert result["severity"] == "HIGH"

    assert result["similarity"] > 0.5
