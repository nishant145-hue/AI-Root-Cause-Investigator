from app.agent.nodes.memory_writer import (
    memory_writer_node,
)


def test_memory_writer_stores_validated_investigation(
    monkeypatch,
):

    captured = {}

    def fake_embed_text(text):
        captured["text"] = text
        return [0.1] * 384

    class FakeVectorStore:

        def ensure_collection(self):
            captured["collection"] = True

        def upsert(
            self,
            investigation_id,
            vector,
            payload,
        ):
            captured["investigation_id"] = (
                investigation_id
            )

            captured["vector"] = vector
            captured["payload"] = payload

    monkeypatch.setattr(
        "app.agent.nodes.memory_writer.embed_text",
        fake_embed_text,
    )

    monkeypatch.setattr(
        "app.agent.nodes.memory_writer.QdrantVectorStore",
        FakeVectorStore,
    )

    state = {
        "investigation_id": 124,
        "user_id": 1,
        "incident_summary": (
            "Payment API error rate increased."
        ),
        "root_cause": (
            "Database connection failure"
        ),
        "failed_component": "payment-api",
        "confidence": 0.82,
        "severity": "HIGH",
        "investigation_status": (
            "ROOT_CAUSE_VALIDATED"
        ),
        "memory_stored": False,
    }

    result = memory_writer_node(state)

    assert result["memory_stored"] is True

    assert captured["collection"] is True

    assert captured["investigation_id"] == 124

    assert len(captured["vector"]) == 384

    assert (
        captured["payload"]["user_id"]
        == 1
    )

    assert (
        captured["payload"]["root_cause"]
        == "Database connection failure"
    )

    assert (
        captured["payload"]["failed_component"]
        == "payment-api"
    )

    assert (
        "Payment API error rate increased."
        in captured["text"]
    )

def test_memory_writer_skips_unvalidated_investigation(
    monkeypatch,
):

    called = False

    def fake_embed_text(text):
        nonlocal called
        called = True
        return [0.1] * 384

    monkeypatch.setattr(
        "app.agent.nodes.memory_writer.embed_text",
        fake_embed_text,
    )

    state = {
        "investigation_id": 125,
        "user_id": 1,
        "incident_summary": "Database failure",
        "root_cause": None,
        "failed_component": None,
        "confidence": None,
        "investigation_status": "IN_PROGRESS",
        "memory_stored": False,
    }

    result = memory_writer_node(state)

    assert result == {}

    assert called is False
