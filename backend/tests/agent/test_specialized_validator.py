from app.agent.agents.validator import ValidatorAgent


def test_validator_agent_name():

    agent = ValidatorAgent()

    assert agent.name == "validator"


def test_validator_agent_role():

    agent = ValidatorAgent()

    assert "Validate" in agent.role


def test_validator_owns_root_cause_validation():

    agent = ValidatorAgent()

    assert agent.owns_capability(
        "validate_root_cause"
    )


def test_validator_does_not_own_log_search():

    agent = ValidatorAgent()

    assert not agent.owns_capability(
        "search_logs"
    )


def test_validator_does_not_own_memory_search():

    agent = ValidatorAgent()

    assert not agent.owns_capability(
        "semantic_memory_search"
    )


def test_validator_rejects_unowned_capability():

    agent = ValidatorAgent()

    try:
        agent.require_capability(
            "search_logs"
        )

        assert False

    except PermissionError:
        assert True


def test_validator_validates_strong_hypothesis():

    agent = ValidatorAgent()

    hypotheses = [
        {
            "cause": "Database connection failure",
            "confidence": 0.82,
            "supporting_evidence": [
                "Database connection timeout",
            ],
            "contradicting_evidence": [],
        },
        {
            "cause": "Application-level failure",
            "confidence": 0.35,
            "supporting_evidence": [
                "Payment API error rate increased",
            ],
            "contradicting_evidence": [],
        },
    ]

    evidence = [
        {
            "message": "Database connection timeout",
        }
    ]

    result = agent.validate_root_cause(
        hypotheses=hypotheses,
        evidence=evidence,
    )

    assert result["validated"] is True

    assert result["root_cause"] == (
        "Database connection failure"
    )

    assert result["confidence"] == 0.82

    assert result["status"] == (
        "ROOT_CAUSE_VALIDATED"
    )


def test_validator_rejects_missing_supporting_evidence():

    agent = ValidatorAgent()

    hypotheses = [
        {
            "cause": "Unknown failure",
            "confidence": 0.90,
            "supporting_evidence": [],
            "contradicting_evidence": [],
        }
    ]

    result = agent.validate_root_cause(
        hypotheses=hypotheses,
        evidence=[],
    )

    assert result["validated"] is False

    assert result["root_cause"] is None

    assert result["status"] == "REJECTED"


def test_validator_rejects_contradicting_evidence():

    agent = ValidatorAgent()

    hypotheses = [
        {
            "cause": "Database failure",
            "confidence": 0.80,
            "supporting_evidence": [
                "Database timeout",
            ],
            "contradicting_evidence": [
                "Database health check passed",
            ],
        }
    ]

    result = agent.validate_root_cause(
        hypotheses=hypotheses,
        evidence=[],
    )

    assert result["validated"] is False

    assert result["root_cause"] is None

    assert result["status"] == "REJECTED"


def test_validator_run():

    agent = ValidatorAgent()

    state = {
        "hypotheses": [
            {
                "cause": "Database connection failure",
                "confidence": 0.82,
                "supporting_evidence": [
                    "Database timeout",
                ],
                "contradicting_evidence": [],
            }
        ],
        "evidence": [
            {
                "message": "Database timeout",
            }
        ],
    }

    result = agent.run(state)

    assert result["agent"] == "validator"

    assert result["validated"] is True

    assert result["root_cause"] == (
        "Database connection failure"
    )

    assert result["confidence"] == 0.82

    assert result["status"] == (
        "ROOT_CAUSE_VALIDATED"
    )
