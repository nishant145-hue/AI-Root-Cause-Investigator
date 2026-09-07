from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from app.core.config import settings
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

VECTOR_SIZE = 384


class QdrantVectorStore:
    """
    Qdrant vector store for investigation memory.

    Supports:

    - in-memory Qdrant for tests/development
    - persistent remote Qdrant for Docker/production
    """

    def __init__(
        self,
        client: QdrantClient | None = None,
    ) -> None:

        if client is not None:

            self.client = client

        elif settings.QDRANT_URL.startswith(
            "memory://"
        ):

            self.client = QdrantClient(
                ":memory:"
            )

        else:

            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=(
                    settings.QDRANT_API_KEY
                    or None
                ),
                timeout=settings.QDRANT_TIMEOUT,
            )

        self.collection_name = (
            settings.QDRANT_COLLECTION
        )

    def ensure_collection(self) -> None:
        """
        Ensure the configured collection exists.

        Handles races where another process/test creates or
        deletes the collection between existence checks and
        creation.
        """

        if self.client.collection_exists(
        self.collection_name
        ):
            return

        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )

            return

        except UnexpectedResponse as exc:

            if exc.status_code != 409:
                raise

            #    A concurrent creator may have won the race.
            # Verify rather than blindly assuming success.
            if self.client.collection_exists(
                self.collection_name
            ):
                return

        # Qdrant may briefly expose the collection state
        # inconsistently during concurrent test/process
        # operations. Retry creation once.
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )

                return

            except UnexpectedResponse as retry_exc:

                if (
                    retry_exc.status_code == 409
                    and self.client.collection_exists(
                        self.collection_name
                    )
                ):
                    return

                raise

    def health_check(self) -> bool:
        """
        Check whether Qdrant is reachable.
        """

        try:

            self.client.get_collections()

            return True

        except Exception:

            return False

    def upsert(
        self,
        investigation_id: int,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """
        Insert or update investigation memory.

        Handles a collection disappearing between the
        existence check and the write.
        """

        if len(vector) != VECTOR_SIZE:
            raise ValueError(
                f"Expected vector dimension "
                f"{VECTOR_SIZE}, "
                f"received {len(vector)}."
            )

        self.ensure_collection()

        point = PointStruct(
            id=investigation_id,
            vector=vector,
            payload=payload,
        )

        try:

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )

        except UnexpectedResponse as exc:

            if exc.status_code != 404:
                raise

        # Collection disappeared between ensure_collection()
        # and upsert(). Recreate it and retry exactly once.
            self.ensure_collection()

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )

    def memory_point_id(
        user_id: int,
        investigation_id: int,
    ) -> UUID:

        return uuid5(
            NAMESPACE_URL,
            f"ai-rca-memory:{user_id}:{investigation_id}",
        )

    def search(
        self,
        vector: list[float],
        limit: int = 5,
        user_id: int | None = None,
    ) -> list[Any]:
        """
        Search semantic investigation memory.

        When user_id is supplied, only that user's
        historical investigations are returned.
        """

        if len(vector) != VECTOR_SIZE:
            raise ValueError(
                f"Expected vector dimension "
                f"{VECTOR_SIZE}, "
                f"received {len(vector)}."
            )

        self.ensure_collection()

        query_filter = None

        if user_id is not None:

            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(
                            value=user_id
                        ),
                    )
                ]
            )

        try:

            results = self.client.query_points(
                collection_name=self.collection_name,
                query=vector,
                query_filter=query_filter,
                limit=limit,
            )

        except UnexpectedResponse as exc:

            if exc.status_code != 404:
                raise

            self.ensure_collection()

            results = self.client.query_points(
                collection_name=self.collection_name,
                query=vector,
                query_filter=query_filter,
                limit=limit,
            )


        return results.points
