from __future__ import annotations

import re
from typing import Any

from sqlmodel import Session, select

from app.models.investigation import (
    Investigation,
    InvestigationStatus,
)


def _tokenize(text: str | None) -> set[str]:
    """
    Convert text into normalized tokens.

    This is intentionally simple for Phase 9.4.1.
    Semantic/vector search will be added later with Qdrant.
    """

    if not text:
        return set()

    return {
        token
        for token in re.findall(
            r"[a-zA-Z0-9_-]+",
            text.lower(),
        )
        if len(token) > 2
    }


def _similarity_score(
    current_text: str,
    historical_text: str,
) -> float:
    """
    Calculate a transparent token-overlap similarity.

    This is NOT a vector similarity score.
    """

    current_tokens = _tokenize(current_text)
    historical_tokens = _tokenize(historical_text)

    if not current_tokens or not historical_tokens:
        return 0.0

    intersection = (
        current_tokens & historical_tokens
    )

    union = (
        current_tokens | historical_tokens
    )

    if not union:
        return 0.0

    return len(intersection) / len(union)


def search_historical_incidents(
    session: Session,
    *,
    current_investigation_id: int,
    user_id: int,
    incident_summary: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Search previous completed investigations belonging
    to the same user.

    The current investigation is excluded.

    Historical investigations are used as context only.
    They must never automatically determine the current
    root cause.
    """

    statement = (
        select(Investigation)
        .where(
            Investigation.user_id == user_id,
            Investigation.status
            == InvestigationStatus.COMPLETED,
            Investigation.id
            != current_investigation_id,
        )
        .order_by(
            Investigation.created_at.desc()
        )
    )

    investigations = list(
        session.exec(statement).all()
    )

    results: list[dict[str, Any]] = []

    for investigation in investigations:

        historical_text = " ".join(
            value
            for value in [
                investigation.title,
                investigation.description,
                investigation.summary,
                investigation.root_cause,
                investigation.failed_component,
            ]
            if value
        )

        similarity = _similarity_score(
            incident_summary,
            historical_text,
        )

        if similarity <= 0:
            continue

        results.append(
            {
                "investigation_id": investigation.id,
                "similarity": round(
                    similarity,
                    4,
                ),
                "summary": (
                    investigation.summary
                    or investigation.description
                    or investigation.title
                ),
                "root_cause": (
                    investigation.root_cause
                    or ""
                ),
                "failed_component": (
                    investigation.failed_component
                    or ""
                ),
                "severity": (
                    investigation.severity
                    or ""
                ),
                "confidence": (
                    investigation.confidence
                ),
            }
        )

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True,
    )

    return results[:limit]
