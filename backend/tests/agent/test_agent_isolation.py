from app.agent.agent_isolation import (
    MAX_REROUTES,
    get_isolated_agents,
    isolate_agent,
    is_agent_isolated,
    record_reroute,
    select_reroute_agent,
)
from app.agent.circuit_breaker import (
    CircuitState,
)


def test_agent_can_be_isolated():
    state = {}

    isolate_agent(
        state,
        "investigator",
    )

    assert is_agent_isolated(
        state,
        "investigator",
    )

    assert (
        "investigator"
        in get_isolated_agents(state)
    )


def test_isolated_agent_is_not_selected():
    state = {
        "isolated_agents": [
            "investigator",
        ],
        "circuit_breaker_states": {
            "investigator": "OPEN",
            "reasoner": "CLOSED",
        },
        "reroute_count": 0,
    }

    target = select_reroute_agent(
        state,
        failed_agent="investigator",
        candidates=[
            "investigator",
            "reasoner",
        ],
    )

    assert target == "reasoner"


def test_failed_agent_is_never_selected():
    state = {
        "isolated_agents": [],
        "circuit_breaker_states": {
            "investigator": "CLOSED",
        },
        "reroute_count": 0,
    }

    target = select_reroute_agent(
        state,
        failed_agent="investigator",
        candidates=[
            "investigator",
        ],
    )

    assert target is None


def test_open_candidate_is_ignored():
    state = {
        "isolated_agents": [],
        "circuit_breaker_states": {
            "reasoner": "OPEN",
            "validator": "CLOSED",
        },
        "reroute_count": 0,
    }

    target = select_reroute_agent(
        state,
        failed_agent="investigator",
        candidates=[
            "reasoner",
            "validator",
        ],
    )

    assert target == "validator"


def test_reroute_count_is_recorded():
    state = {
        "reroute_count": 0,
    }

    record_reroute(
        state,
        failed_agent="investigator",
        target_agent="reasoner",
    )

    assert state["reroute_count"] == 1
    assert (
        state["last_rerouted_agent"]
        == "investigator"
    )
    assert (
        state["next_agent"]
        == "reasoner"
    )


def test_reroute_limit_prevents_loop():
    state = {
        "isolated_agents": [],
        "circuit_breaker_states": {
            "reasoner": "CLOSED",
        },
        "reroute_count": MAX_REROUTES,
    }

    target = select_reroute_agent(
        state,
        failed_agent="investigator",
        candidates=[
            "reasoner",
        ],
    )

    assert target is None
