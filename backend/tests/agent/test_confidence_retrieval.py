from types import SimpleNamespace

from app.vectorstore.retriever import (
    InvestigationRetriever,
)


class FakeVectorStore:

    def search(
        self,
        vector,
        limit=5,
        user_id=None,
    ):

        return [
            SimpleNamespace(
                score=0.95,
                payload={
                    "investigation_id": 1,
                    "user_id": 1,
                    "summary": "Old database incident",
                    "root_cause": "Database failure",
                    "failed_component": "database",
                    "severity": "HIGH",
                    "confidence": 0.40,
                    "validated": False,
                    "evidence_count": 0,
                    "age_days": 500,
                },
            ),
            SimpleNamespace(
                score=0.88,
                payload={
                    "investigation_id": 2,
                    "user_id": 1,
                    "summary": "Recent database incident",
                    "root_cause": "Database pool exhaustion",
                    "failed_component": "database",
                    "severity": "HIGH",
                    "confidence": 0.90,
                    "validated": True,
                    "evidence_count": 4,
                    "age_days": 10,
                },
            ),
        ]


def test_confidence_aware_retrieval(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.vectorstore.retriever.embed_text",
        lambda text: [0.1] * 384,
    )

    retriever = InvestigationRetriever(
        vector_store=FakeVectorStore()
    )

    results = retriever.search(
        query="database connection failure",
        user_id=1,
    )

    assert len(results) == 1

    result = results[0]

    assert result[
        "investigation_id"
    ] == 2

    assert result[
        "memory_status"
    ] == "RELIABLE"

    assert result[
        "memory_quality"
    ] >= 0.80

    assert result[
        "ranking_score"
    ] > 0.80
