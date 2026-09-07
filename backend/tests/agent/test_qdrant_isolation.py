from app.embeddings.huggingface_embeddings import (
    embed_text,
)
from app.vectorstore.qdrant_client import (
    QdrantVectorStore,
)
from app.vectorstore.retriever import (
    InvestigationRetriever,
)


def test_qdrant_retrieval_is_user_isolated():

    vector_store = QdrantVectorStore()

    vector_store.ensure_collection()

    # ---------------------------------------------------------
    # User 1 investigation
    # ---------------------------------------------------------

    vector_user_1 = embed_text(
        "Payment API database connection failure"
    )

    vector_store.upsert(
        investigation_id=101,
        vector=vector_user_1,
        payload={
            "investigation_id": 101,
            "user_id": 1,
            "summary": (
                "Payment API database failure"
            ),
            "root_cause": (
                "Database connection pool exhaustion"
            ),
            "failed_component": "payment-api",
            "severity": "HIGH",
            "confidence": 0.91,
        },
    )

    # ---------------------------------------------------------
    # User 2 investigation
    # ---------------------------------------------------------

    vector_user_2 = embed_text(
        "Payment API database connection failure"
    )

    vector_store.upsert(
        investigation_id=202,
        vector=vector_user_2,
        payload={
            "investigation_id": 202,
            "user_id": 2,
            "summary": (
                "Payment API database failure"
            ),
            "root_cause": (
                "Database connection pool exhausted"
            ),
            "failed_component": "payment-api",
            "severity": "HIGH",
            "confidence": 0.88,
        },
    )

    retriever = InvestigationRetriever(
        vector_store=vector_store
    )

    # ---------------------------------------------------------
    # User 1 searches
    # ---------------------------------------------------------

    user_1_results = retriever.search(
        query=(
            "Payment API database connection timeout"
        ),
        limit=5,
        user_id=1,
    )

    assert len(user_1_results) == 1

    assert (
        user_1_results[0][
            "investigation_id"
        ]
        == 101
    )

    assert (
        user_1_results[0]["user_id"]
        == 1
    )

    # ---------------------------------------------------------
    # User 2 searches
    # ---------------------------------------------------------

    user_2_results = retriever.search(
        query=(
            "Payment API database connection timeout"
        ),
        limit=5,
        user_id=2,
    )

    assert len(user_2_results) == 1

    assert (
        user_2_results[0][
            "investigation_id"
        ]
        == 202
    )

    assert (
        user_2_results[0]["user_id"]
        == 2
    )

    # ---------------------------------------------------------
    # Cross-user isolation
    # ---------------------------------------------------------

    assert all(
        result["user_id"] == 1
        for result in user_1_results
    )

    assert all(
        result["user_id"] == 2
        for result in user_2_results
    )
