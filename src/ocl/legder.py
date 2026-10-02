from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, TypeAdapter

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
        with self.path.open() as f:
            return [_adapter.validate_json(line) for line in f if line.strip()]