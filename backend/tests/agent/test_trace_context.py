from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.agent.trace_context import (
    TraceContext,
    child_trace_context,
    clear_trace_context,
    create_trace_context,
    create_child_trace_context,
    get_or_create_trace_context,
    get_trace_context,
    trace_context,
)


def test_create_root_trace_context():
    context = create_trace_context()

    assert context.trace_id
    assert context.span_id

    assert (
        context.parent_span_id
        is None
    )


def test_child_context_preserves_trace_id():
    parent = create_trace_context()

    child = parent.child()

    assert (
        child.trace_id
        == parent.trace_id
    )

    assert (
        child.span_id
        != parent.span_id
    )

    assert (
        child.parent_span_id
        == parent.span_id
    )


def test_get_or_create_context_creates_root():
    clear_trace_context()

    context = (
        get_or_create_trace_context()
    )

    assert context.trace_id
    assert context.span_id

    current = get_trace_context()

    assert current == context

    clear_trace_context()


def test_trace_context_restores_previous_context():
    clear_trace_context()

    outer = create_trace_context()

    with trace_context(outer):

        assert (
            get_trace_context()
            == outer
        )

        inner = create_trace_context()

        with trace_context(inner):

            assert (
                get_trace_context()
                == inner
            )

        assert (
            get_trace_context()
            == outer
        )

    assert (
        get_trace_context()
        is None
    )


def test_child_trace_context_restores_parent():
    clear_trace_context()

    parent = create_trace_context()

    with trace_context(parent):

        with child_trace_context() as child:

            assert (
                child.trace_id
                == parent.trace_id
            )

            assert (
                child.span_id
                != parent.span_id
            )

            assert (
                child.parent_span_id
                == parent.span_id
            )

            assert (
                get_trace_context()
                == child
            )

        assert (
            get_trace_context()
            == parent
        )

    clear_trace_context()


def test_create_child_trace_context():
    clear_trace_context()

    parent = create_trace_context()

    with trace_context(parent):

        child = (
            create_child_trace_context()
        )

        assert (
            child.trace_id
            == parent.trace_id
        )

        assert (
            child.parent_span_id
            == parent.span_id
        )

        assert (
            get_trace_context()
            == child
        )

    clear_trace_context()


def test_context_isolation_between_threads():
    clear_trace_context()

    from threading import Barrier

    barrier = Barrier(2)

    def worker():
        clear_trace_context()

        context = (
            get_or_create_trace_context()
        )

        barrier.wait(timeout=5)

        return (
            context.trace_id,
            context.span_id,
        )

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        first = executor.submit(
            worker
        )

        second = executor.submit(
            worker
        )

        first_trace_id, first_span_id = (
            first.result(timeout=5)
        )

        second_trace_id, second_span_id = (
            second.result(timeout=5)
        )

    assert first_trace_id
    assert second_trace_id

    assert first_span_id
    assert second_span_id

    assert (
        first_trace_id
        != second_trace_id
    )

    assert (
        first_span_id
        != second_span_id
    )

    clear_trace_context()


def test_clear_trace_context():
    context = create_trace_context()

    with trace_context(context):

        assert (
            get_trace_context()
            == context
        )

        clear_trace_context()

        assert (
            get_trace_context()
            is None
        )


def test_trace_context_to_dict():
    context = TraceContext(
        trace_id="trace-123",
        span_id="span-456",
        parent_span_id="span-000",
    )

    data = context.to_dict()

    assert data == {
        "trace_id": "trace-123",
        "span_id": "span-456",
        "parent_span_id": "span-000",
    }
