import time
import uuid

from app.core.metrics import metrics
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 128


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a safe request ID and correlate request logs."""

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        request_id = request.headers.get(
            REQUEST_ID_HEADER
        )

        if (
            not request_id
            or len(request_id) > MAX_REQUEST_ID_LENGTH
        ):
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        start_time = time.perf_counter()

        with logger.contextualize(
            request_id=request_id
        ):
            logger.info(
                "request_started "
                f"method={request.method} "
                f"path={request.url.path}"
            )

            try:
                response = await call_next(request)

                duration_ms = (
                    time.perf_counter() - start_time
                ) * 1000
                
                metrics.record_request(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )
                logger.info(
                    "request_completed "
                    f"method={request.method} "
                    f"path={request.url.path} "
                    f"status={response.status_code} "
                    f"duration_ms={duration_ms:.2f}"
                )

            except Exception:
                duration_ms = (
                    time.perf_counter() - start_time
                ) * 1000

                logger.exception(
                    "request_failed "
                    "method={} path={} "
                    "duration_ms={:.2f}",
                    request.method,
                    request.url.path,
                    duration_ms,
                )

                raise

        response.headers[REQUEST_ID_HEADER] = request_id

        return response