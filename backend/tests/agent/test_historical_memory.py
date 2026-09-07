from app.agent.memory.historical_memory import (
    HistoricalMemoryService,
)
from app.vectorstore.qdrant_client import (
    QdrantVectorStore,
)
from app.vectorstore.retriever import (
    InvestigationRetriever,
)


def test_store_completed_investigation():

    vector_store = QdrantVectorStore()

    service = HistoricalMemoryService(
        vector_store=vector_store,
    )

    investigation = {
        "investigation_id": 125,
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
        "evidence": [
            "Database connection timeout",
            "Connection pool reached 99%",
        ],
        "recommendations": [
            "Increase database connection pool",
            "Review recent deployment",
        ],
        "additional_notes": (
            "Similar incidents were observed "
            "after configuration changes."
        ),
    }

    # Store investigation in semantic memory.
    service.store_investigation(
        investigation
    )

    # Search semantic memory.
    retriever = InvestigationRetriever(
        vector_store=vector_store
    )

    matches = retriever.search(
        "Payment API database connection timeout",
        limit=5,
    )

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    assert len(matches) == 1

    assert (
        matches[0]["investigation_id"]
        == 125
    )

    assert (
        matches[0]["root_cause"]
        == "Database connection pool exhaustion"
    )

    assert (
        matches[0]["failed_component"]
        == "payment-api"
    )

    assert matches[0]["severity"] == "HIGH"

    assert matches[0]["confidence"] == 0.91
