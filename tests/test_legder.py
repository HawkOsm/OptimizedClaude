import json
from datetime import UTC, datetime

from freezegun import freeze_time

from ocl.events.route_decision import RouteDecision
from ocl.events.user_input import UserInput
from ocl.legder import Ledger


@freeze_time("2023-01-01 12:00:00")
def test_user_input_roundtrip(tmp_path: str) -> None:
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
    
def test_input_validation(tmp_path: str) -> None:
    # Create a temporary file path
    invalid_file = tmp_path / "test_ledger.txt"
    valid_file = tmp_path / "test_ledger_valid.txt"

    # Initialize Ledger with the temporary file path
    invalid_ledger = Ledger(path=invalid_file)
    valid_ledger = Ledger(path=valid_file)

    # Create a UserInput instance with invalid data (missing required field)
    invalid_user_input = {
        "event": "user_input",
        "text": "Test input",
    }  # Missing session_id
    validated_event = {
        "event": "user_input",
        "text": "Test input",
        "session_id": None,
    }

    # Directly write the invalid data to the ledger file
    with invalid_file.open("a") as f:
        f.write(json.dumps(invalid_user_input) + "\n")
    with valid_file.open("a") as f:
        f.write(json.dumps(validated_event) + "\n")
    # Read the contents of the ledger
    contents = invalid_ledger.read()
    assert len(contents) == 0
    event = valid_ledger.read().pop()
    assert event.text == "Test input"
    assert event.session_id is None

    
   

    