from datetime import UTC, datetime

from freezegun import freeze_time

from ocl.events import RouteDecision, UserInput
from ocl.legder import Ledger


def test_user_input_roundtrip(tmp_path: str) -> None:
    freezer = freeze_time("2023-01-01 12:00:00")
    frozen_time = freezer.start()
    # Create a temporary file path
    temp_file = tmp_path / "test_ledger.txt"

    # Initialize Ledger with the temporary file path
    ledger = Ledger(str(temp_file))

    # Create a UserInput instance
    user_input = UserInput("Test input")
    route_decision = RouteDecision(confidence=0.95, 
                                   source="heuristics", 
                                   route_class="task_new")

    # Expected latency
    latency = route_decision.latency_ms
    
    ledger.emit(user_input)
    ledger.emit(route_decision)
    timestamp = datetime.fromisoformat("2023-01-01 12:00:00"
                                       ).replace(tzinfo=UTC).isoformat()
    frozen_time.tick()  # Advance time by 1 second
    # Read the contents of the ledger
    contents = ledger.read()
    
    # Assert that the contents match the emitted input
    assert UserInput("Test input", timestamp=timestamp).json() \
        == contents[0].json() \
        and RouteDecision(confidence=0.95, 
                          source="heuristics", 
                          route_class="task_new",
                          latency_ms=latency,
                          timestamp=timestamp).json() \
        == contents[1].json()
    
