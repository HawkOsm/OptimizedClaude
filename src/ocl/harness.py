from collections.abc import Callable
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Router = Callable[[str, bool], str]


class CaseResult(BaseModel):
    id: int
    message: str
    session_active: bool
    expected: Literal["TASK_NEW", "PASSTHROUGH", "TRIVIAL"]
    got: Literal["TASK_NEW", "PASSTHROUGH", "TRIVIAL"]
    correct: bool
    must_pass: bool
    latency_ms: float = 0.0
    run_at: datetime = Field(default_factory=datetime.now)
    error: str | None = None


class Report(BaseModel):
    router_name: str
    run_at: datetime
    results: list[CaseResult]

    @property
    def total(self) -> int:
        """Return the number of cases in the report."""
        return len(self.results)

    @property
    def correct(self) -> int:
        """Return the number of cases classified correctly."""
        return sum(result.correct for result in self.results)

    @property
    def accuracy(self) -> float:
        """Return accuracy as a value between zero and one."""
        return self.correct / self.total if self.total else 0.0

    @property
    def must_passed(self) -> bool:
        """Return whether every required case passed."""
        return all(result.correct for result in self.results if result.must_pass)

    def summary(self) -> dict[str, object]:
        """Return a compact, serialization-friendly report summary."""
        return {
            "router_name": self.router_name,
            "total": self.total,
            "correct": self.correct,
            "accuracy": self.accuracy,
            "must_passed": self.must_passed,
        }


def run(router: Router, cases: list[CaseResult], name: str) -> Report:
    for case in cases:
        started = datetime.now()
        try:
            decision = router(case.message, case.session_active)
            case.got = decision
            case.correct = decision == case.expected
        except Exception as exc:
            case.correct = False
            case.error = str(exc)
        case.latency_ms = (datetime.now() - started).total_seconds() * 1000

    report = Report(
        router_name=getattr(router, "name", name), run_at=datetime.now(), results=cases
    )
    return report
