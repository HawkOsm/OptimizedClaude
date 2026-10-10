from pathlib import Path

from ocl.golden import Golden
from ocl.harness import CaseResult, run


def passthrough_router(message: str, session_active: bool) -> str:
    return "PASSTHROUGH"


def test_run_passthrough_router_against_golden_cases() -> None:
    golden = Golden()
    golden.load_router_cases_from_json(
        Path(__file__).parent / "golden" / "router_cases.jsonl"
    )
    cases = [
        CaseResult(
            id=case.id,
            message=case.message,
            session_active=case.session_active,
            expected=case.expected,
            got="PASSTHROUGH",
            correct=False,
            must_pass=case.must_pass is True,
        )
        for case in golden.router_cases
    ]

    report = run(passthrough_router, cases, name="passthrough")

    expected_correct = sum(
        case.expected == "PASSTHROUGH" for case in golden.router_cases
    )
    assert report.router_name == "passthrough"
    assert report.total == len(golden.router_cases)
    assert report.correct == expected_correct
    assert report.accuracy == expected_correct / report.total
    assert report.must_passed is True
    assert all(result.got == "PASSTHROUGH" for result in report.results)
    assert all(result.error is None for result in report.results)
    assert all(result.latency_ms >= 0 for result in report.results)
