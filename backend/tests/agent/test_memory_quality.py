from app.agent.memory.quality import (
    calculate_memory_quality,
    classify_memory_quality,
)


def test_high_quality_memory():

    score = calculate_memory_quality(
        similarity=0.95,
        confidence=0.95,
        age_days=10,
        validated=True,
        evidence_count=4,
    )

    assert score >= 0.80

    assert classify_memory_quality(
        score
    ) == "RELIABLE"


def test_medium_quality_memory():

    score = calculate_memory_quality(
        similarity=0.75,
        confidence=0.70,
        age_days=60,
        validated=True,
        evidence_count=2,
    )

    assert 0.60 <= score < 0.80

    assert classify_memory_quality(
        score
    ) == "USEFUL"


def test_stale_memory():

    score = calculate_memory_quality(
        similarity=0.50,
        confidence=0.40,
        age_days=500,
        validated=False,
        evidence_count=0,
    )

    assert score < 0.40

    assert classify_memory_quality(
        score
    ) == "STALE"
