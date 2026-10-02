from datetime import UTC, datetime

from freezegun import freeze_time

from ocl.events.route_decision import RouteDecision
from ocl.events.user_input import UserInput
from ocl.legder import Ledger


def test_user_input_roundtrip(tmp_path: str) -> None:
    freezer = freeze_time("2023-01-01 12:00:00")
    frozen_time = freezer.start()
    # Create a temporary file path
    temp_file = tmp_path / "test_ledger.txt"

    # Initialize Ledger with the temporary file path
    ledger = Ledger(path=temp_file)

    # Create a UserInput instance
    user_input = UserInput(text="Test input", session_id="session_123")
    route_decision = RouteDecision(confidence=0.95,
                                   source="heuristics",
                                   route_class="passthrough",
                                   session_id="session_123")

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
    assert UserInput(text="Test input", 
                     timestamp=timestamp, 
                     session_id="session_123").model_dump_json() \
        == contents[0].model_dump_json() \
        and RouteDecision(confidence=0.95, 
                          source="heuristics", 
                          route_class="passthrough",
                          latency_ms=latency,
                          timestamp=timestamp,
                          session_id="session_123").model_dump_json() \
        == contents[1].model_dump_json()
    
