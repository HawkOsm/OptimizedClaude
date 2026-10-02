from datetime import UTC, datetime

from pydantic import BaseModel, Field


class Events(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    session_id: str | None