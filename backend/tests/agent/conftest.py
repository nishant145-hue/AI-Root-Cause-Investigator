import pytest
from qdrant_client.models import Filter

from app.core.config import settings
from app.vectorstore.qdrant_client import QdrantVectorStore


TEST_COLLECTION = "investigation_memory_test"


@pytest.fixture(scope="session", autouse=True)
def configure_qdrant_test_collection():
    """
    Configure one isolated Qdrant collection for the complete agent
    test session.

    The collection is created once at session startup and deleted once
    at session teardown.
    """

    original_collection = settings.QDRANT_COLLECTION
    settings.QDRANT_COLLECTION = TEST_COLLECTION

    vector_store = QdrantVectorStore()

    try:
        # Remove a stale collection from a previous test session.
        try:
            if vector_store.client.collection_exists(
                TEST_COLLECTION
            ):
                vector_store.client.delete_collection(
                    collection_name=TEST_COLLECTION
                )
        except Exception:
            pass

        # Create the isolated test collection once.
        vector_store.ensure_collection()

        yield

    finally:
        # Remove the test collection once after the complete session.
        try:
            if vector_store.client.collection_exists(
                TEST_COLLECTION
            ):
                vector_store.client.delete_collection(
                    collection_name=TEST_COLLECTION
                )
        except Exception:
            pass

        settings.QDRANT_COLLECTION = original_collection


@pytest.fixture(autouse=True)
def clean_qdrant_test_data():
    """
    Clear all points before every agent test.

    This preserves test-level data isolation without repeatedly
    deleting and recreating the Qdrant collection.
    """

    vector_store = QdrantVectorStore()

    try:
        vector_store.client.delete(
            collection_name=TEST_COLLECTION,
            points_selector=Filter(),
        )
    except Exception:
        pass

    yield
