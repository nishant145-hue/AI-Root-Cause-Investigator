def calculate_memory_quality(
    *,
    similarity: float,
    confidence: float,
    age_days: float = 0.0,
    validated: bool = True,
    evidence_count: int = 1,
) -> float:
    """
    Calculate the reliability of a historical investigation.

    Score range:
        0.0 -> very weak memory
        1.0 -> highly reliable memory
    """

    similarity = max(
        0.0,
        min(1.0, float(similarity)),
    )

    confidence = max(
        0.0,
        min(1.0, float(confidence)),
    )

    # ---------------------------------------------------------
    # Semantic similarity
    # ---------------------------------------------------------

    similarity_score = similarity

    # ---------------------------------------------------------
    # Historical confidence
    # ---------------------------------------------------------

    confidence_score = confidence

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    validation_score = (
        1.0
        if validated
        else 0.2
    )

    # ---------------------------------------------------------
    # Evidence quality
    # ---------------------------------------------------------

    if evidence_count <= 0:
        evidence_score = 0.2
    elif evidence_count == 1:
        evidence_score = 0.7
    elif evidence_count == 2:
        evidence_score = 0.85
    else:
        evidence_score = 1.0

    # ---------------------------------------------------------
    # Freshness / staleness
    # ---------------------------------------------------------

    if age_days <= 30:
        freshness_score = 1.0

    elif age_days <= 90:
        freshness_score = 0.85

    elif age_days <= 180:
        freshness_score = 0.70

    elif age_days <= 365:
        freshness_score = 0.55

    else:
        freshness_score = 0.20

    # ---------------------------------------------------------
    # Weighted quality
    # ---------------------------------------------------------

    quality = (
        similarity_score * 0.35
        + confidence_score * 0.30
        + validation_score * 0.15
        + evidence_score * 0.10
        + freshness_score * 0.10
    )

    return round(
        max(
            0.0,
            min(1.0, quality),
        ),
        4,
    )


def classify_memory_quality(
    score: float,
) -> str:
    """
    Classify historical memory quality.
    """

    score = float(score)

    if score >= 0.80:
        return "RELIABLE"

    if score >= 0.60:
        return "USEFUL"

    if score >= 0.40:
        return "WEAK"

    return "STALE"
