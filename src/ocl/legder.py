from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from ocl.events.base import Events
from ocl.events.route_decision import RouteDecision
from ocl.events.user_input import UserInput

EventUnion = Annotated[UserInput | RouteDecision, Field(discriminator="event")]
_adapter: TypeAdapter[EventUnion] = TypeAdapter(EventUnion)


class Ledger(BaseModel):
    path: Path

    def emit(self, event: Events) -> None:
        with self.path.open("a") as f:
            f.write(event.model_dump_json() + "\n")

    def read(self) -> list[Events]:
        events: list[Events] = []
        with self.path.open() as f:
            for line in f:
                validated_event = self.validate_line(line.strip())
                if validated_event is not None:
                    events.append(validated_event)
        return events

    def validate_line(self, line: str) -> Events | None:    
        try:
            adapted_event = _adapter.validate_json(line)
            return adapted_event if isinstance(adapted_event, Events) else None
        except ValidationError:
            return None

     