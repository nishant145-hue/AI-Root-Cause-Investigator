from app.vectorstore.qdrant_client import (
    QdrantVectorStore,
)


def test_qdrant_health():

    vector_store = QdrantVectorStore()

    assert vector_store.health_check() is True


def test_qdrant_collection_creation():

    vector_store = QdrantVectorStore()

    vector_store.ensure_collection()

    collections = (
        vector_store.client
        .get_collections()
    )

    names = {
        collection.name
        for collection in (
            collections.collections
        )
    }

    assert (
        vector_store.collection_name
        in names
    )


def test_qdrant_rejects_wrong_vector_size():

    vector_store = QdrantVectorStore()

    vector_store.ensure_collection()

    try:

        vector_store.upsert(
            investigation_id=999,
            vector=[0.1, 0.2],
            payload={
                "investigation_id": 999,
                "user_id": 1,
            },
        )

        assert False

    except ValueError as exc:

        assert "384" in str(exc)
