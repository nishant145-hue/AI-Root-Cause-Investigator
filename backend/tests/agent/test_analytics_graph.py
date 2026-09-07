from app.agent.graph import (
    build_investigation_graph,
)


def test_graph_contains_analytics_node():

    graph = build_investigation_graph(
        session=None,
    )

    nodes = graph.nodes

    assert "analytics" in nodes


def test_graph_routes_memory_writer_to_analytics():

    graph = build_investigation_graph(
        session=None,
    )

    edges = graph.get_graph().edges

    memory_writer_edges = [
        edge
        for edge in edges
        if edge.source == "memory_writer"
    ]

    assert len(
        memory_writer_edges
    ) == 1

    assert (
        memory_writer_edges[0].target
        == "analytics"
    )


def test_graph_routes_analytics_to_end():

    graph = build_investigation_graph(
        session=None,
    )

    edges = graph.get_graph().edges

    analytics_edges = [
        edge
        for edge in edges
        if edge.source == "analytics"
    ]

    assert len(
        analytics_edges
    ) == 1

    assert (
        analytics_edges[0].target
        == "__end__"
    )

from app.agent.nodes.analytics import (
    analytics_node,
)


def test_analytics_node_produces_state_update():

    state = {
        "execution_timeline": [
            {
                "agent": "planner",
                "status": "COMPLETED",
                "duration_ms": 100.0,
                "attempt": 1,
            },
            {
                "agent": "reasoner",
                "status": "COMPLETED",
                "duration_ms": 200.0,
                "attempt": 1,
            },
        ]
    }

    result = analytics_node(
        state
    )

    assert (
        "execution_analytics"
        in result
    )

    analytics = result[
        "execution_analytics"
    ]

    assert (
        analytics[
            "execution"
        ][
            "total_executions"
        ]
        == 2
    )

    assert (
        analytics[
            "efficiency"
        ][
            "rating"
        ]
        == "EXCELLENT"
    )
