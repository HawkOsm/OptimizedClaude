from datetime import UTC, datetime
from typing import Literal

from pydantic import Field, ValidationInfo, field_validator

from ocl.events.base import Events


class RouteDecision(Events):
    event: Literal["route_decision"] = "route_decision"
    source: Literal["heuristics", "llm", "fallback"]
    route_class: Literal["passthrough", "task_new", "trivial", "meta"]
    confidence: float | None = None
    latency_ms: float | None = Field(default=None, validate_default=True)

    @field_validator("latency_ms", mode="before")
    @classmethod
    def fill_latency(cls, v: float | None, info: ValidationInfo) -> float:
        if v is not None:
            return v  # latency was given — use it as-is
        ts = info.data.get("timestamp", datetime.now(UTC))
        if not ts.tzinfo:
            ts = ts.replace(tzinfo=UTC)
        return (datetime.now(UTC) - ts).total_seconds() * 1000
