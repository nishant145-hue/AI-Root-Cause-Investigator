from app.agent.distributed_state import (
    DistributedExecutionState,
)


def test_investigation_state_is_created():

    state = DistributedExecutionState()

    snapshot = state.snapshot(1)

    assert snapshot[
        "investigation_id"
    ] == 1

    assert snapshot[
        "active_tasks"
    ] == 0


def test_started_task_is_tracked():

    state = DistributedExecutionState()

    state.mark_started(
        1,
        agent_name="investigator",
    )

    snapshot = state.snapshot(1)

    assert snapshot[
        "active_tasks"
    ] == 1

    assert snapshot[
        "last_agent"
    ] == "investigator"


def test_completed_task_is_tracked():

    state = DistributedExecutionState()

    state.mark_started(
        1,
        agent_name="investigator",
    )

    state.mark_completed(1)

    snapshot = state.snapshot(1)

    assert snapshot[
        "active_tasks"
    ] == 0

    assert snapshot[
        "completed_tasks"
    ] == 1


def test_failed_task_is_tracked():

    state = DistributedExecutionState()

    state.mark_started(
        1,
        agent_name="reasoner",
    )

    state.mark_failed(1)

    snapshot = state.snapshot(1)

    assert snapshot[
        "active_tasks"
    ] == 0

    assert snapshot[
        "failed_tasks"
    ] == 1


def test_multiple_investigations_are_isolated():

    state = DistributedExecutionState()

    state.mark_started(
        1,
        agent_name="investigator",
    )

    state.mark_started(
        2,
        agent_name="reasoner",
    )

    first = state.snapshot(1)
    second = state.snapshot(2)

    assert first[
        "active_tasks"
    ] == 1

    assert second[
        "active_tasks"
    ] == 1

    assert first[
        "last_agent"
    ] == "investigator"

    assert second[
        "last_agent"
    ] == "reasoner"


def test_remove_investigation():

    state = DistributedExecutionState()

    state.mark_started(1)

    state.remove(1)

    snapshot = state.snapshot(1)

    assert snapshot[
        "active_tasks"
    ] == 0

def test_concurrent_investigations_are_isolated_under_load():

    from concurrent.futures import ThreadPoolExecutor

    state = DistributedExecutionState()

    investigation_ids = list(range(1, 11))
    tasks_per_investigation = 20

    def run_investigation(investigation_id):

        for _ in range(tasks_per_investigation):

            state.mark_started(
                investigation_id,
                agent_name="investigator",
            )

            state.mark_completed(investigation_id)

    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [
            executor.submit(
                run_investigation,
                investigation_id,
            )
            for investigation_id in investigation_ids
        ]

        for future in futures:
            future.result()

    for investigation_id in investigation_ids:

        snapshot = state.snapshot(investigation_id)

        assert snapshot[
            "active_tasks"
        ] == 0

        assert snapshot[
            "completed_tasks"
        ] == tasks_per_investigation

        assert snapshot[
            "failed_tasks"
        ] == 0

        assert snapshot[
            "last_agent"
        ] == "investigator"
