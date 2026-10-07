import json
from collections import Counter

from ocl.golden import Golden


def test_loading_from_file() -> None:
    """
    Test loading the Golden model from a JSON file.
    """
    clarifier_path = "./tests/golden/clarifier_cases.jsonl"
    router_path = "./tests/golden/router_cases.jsonl"
    golden = Golden()
    golden.load_clarifier_cases_from_json(clarifier_path)
    golden.load_router_cases_from_json(router_path)

    with open(router_path) as f:
        router_raw = [json.loads(line) for line in f if line.strip()]
    with open(clarifier_path) as f:
        clarifier_raw = [json.loads(line) for line in f if line.strip()]
    clarifier_ids = {case["id"] for case in clarifier_raw}
    router_ids = {case["id"] for case in router_raw}
    session_active_count = Counter(case.get("session_active") for case in router_raw)
    must_pass_count = Counter(case.get("must_pass") for case in router_raw)

    assert clarifier_ids == {case.id for case in golden.clarifier_cases}
    assert router_ids == {case.id for case in golden.router_cases}
    assert (
        Counter(case.session_active for case in golden.router_cases)
        == session_active_count
    )
    assert Counter(case.must_pass for case in golden.router_cases) == must_pass_count
