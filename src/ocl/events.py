import enum
from datetime import UTC, datetime
from typing import override


class Events:
    def __init__(self, timestamp: str = None) -> None:
        self.timestamp = datetime.now(tz=UTC).isoformat() \
                        if timestamp is None else timestamp
        self.session_id = None  # Placeholder for session ID, can be set later if needed

    def json(self) -> dict:
        pass  # This method should be overridden in subclasses to return a JSON dict
        

class UserInput(Events):
    def __init__(self, text: str, timestamp: str = None) -> None:
        super().__init__(timestamp)
        self.text = text

    @override
    def json(self) -> dict:
        return {"v": 1, 
                "ts": self.timestamp,
                "session_id": self.session_id, 
                "event": "user_input", 
                "text": self.text}


class RouteSource(enum.Enum):
    HEURISTICS = "heuristics"
    LLM = "llm"
    FALLBACK = "fallback"

class RouteClass(enum.Enum):
    PASSTHROUGH = "passthrough"
    TASK_NEW = "task_new"
    TRIVIAL = "trivial"
    META = "meta"

class RouteDecision(Events):
    def __init__(self,confidence: float = None, 
                 source: RouteSource = None, 
                 route_class: RouteClass = None,
                 latency_ms: float = None,
                 timestamp: str = None
                 ) -> None:
        
        super().__init__(timestamp)
        self.confidence = confidence
        self.source = source
        self.route_class = route_class
        # Calculate latency in millisecond
        self.latency_ms = self.calculate_latency() if latency_ms is None else latency_ms


    @override
    def json(self) -> dict:
        return {"v": 1, 
                "ts": self.timestamp,
                "latency": self.latency_ms, 
                "session_id": self.session_id, 
                "event": "route_decision", 
                "confidence": self.confidence, 
                "source": self.source, 
                "route_class": self.route_class}

    def calculate_latency(self) -> float:
        parsed_time = t if (
            t := datetime.fromisoformat(self.timestamp)
            ).tzinfo \
            is not None else t.replace(tzinfo=UTC)

        return (
            datetime.now(UTC) - parsed_time
        ).total_seconds() * 1000