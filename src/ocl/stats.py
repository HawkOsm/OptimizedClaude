
from typing import Literal

from pydantic import BaseModel

from ocl.events.base import Events


class Stats(BaseModel):

    user_inputs: int = 0
    route_decisions: int = 0
    route_class_counts: dict[
        Literal["passthrough", "task_new", "trivial", "meta"], int
    ] = {}
    source_counts: dict[Literal["heuristics", "llm", "fallback"], int] = {}
    # difference between the first and last timestamps in milliseconds
    wall_clock: int = 0

    def __init__(self, data: list[Events] | None = None, **kwargs: dict) -> None:
        super().__init__(**kwargs)
        events = data if data is not None else []
        if not events:
            return
        for event in events:
            self._count(event)
        timestamps = [event.timestamp for event in events]
        span = max(timestamps) - min(timestamps)
        self.wall_clock = int(span.total_seconds() * 1000)

    def _count(self, event: Events) -> None:
        if event.event == "user_input":
            self.user_inputs += 1
        elif event.event == "route_decision":
            self.route_decisions += 1
            route = event.route_class
            self.route_class_counts[route] = self.route_class_counts.get(route, 0) + 1
            source = event.source
            self.source_counts[source] = self.source_counts.get(source, 0) + 1
