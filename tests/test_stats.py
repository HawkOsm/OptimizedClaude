from datetime import UTC

from ocl.stats import Stats


def test_stats_initialization() -> None:
    # Test initialization with no data
    stats = Stats()
    assert stats.user_inputs == 0
    assert stats.route_decisions == 0
    assert stats.route_class_counts == {}
    assert stats.source_counts == {}
    assert stats.wall_clock == 0


def test_stats_with_data() -> None:
    # Create mock events
    from datetime import datetime, timedelta

    from ocl.events.route_decision import RouteDecision
    from ocl.events.user_input import UserInput

    now = datetime.now(UTC)
    events = [
        UserInput(text="Test input 1", session_id="session_1", timestamp=now),
        RouteDecision(
            confidence=0.9,
            source="heuristics",
            route_class="passthrough",
            session_id="session_1",
            timestamp=now + timedelta(seconds=1),
        ),
        UserInput(
            text="Test input 2",
            session_id="session_2",
            timestamp=now + timedelta(seconds=2),
        ),
        RouteDecision(
            confidence=0.8,
            source="llm",
            route_class="task_new",
            session_id="session_2",
            timestamp=now + timedelta(seconds=3),
        ),
    ]

    stats = Stats(data=events)

    assert stats.user_inputs == 2
    assert stats.route_decisions == 2
    assert stats.route_class_counts == {"passthrough": 1, "task_new": 1}
    assert stats.source_counts == {"heuristics": 1, "llm": 1}
    assert stats.wall_clock == 3000  # 3 seconds in milliseconds
