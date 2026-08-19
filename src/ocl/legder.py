import json

from .events import Events, RouteDecision, UserInput


class Ledger:
    def __init__(self, path: str) -> None:
        self.path = path

    def emit(self, event: Events) -> None:
        event_json = event.json()
        with open(self.path, 'a') as f:
            f.write(json.dumps(event_json) + '\n')

    @classmethod
    def from_dict(cls, data: dict) -> Events:
        event_type = data.get("event")
        if event_type == "user_input":
            return UserInput(text=data.get("text"), timestamp=data.get("ts"))
        elif event_type == "route_decision":
            return RouteDecision(confidence=data.get("confidence"), 
                                 source=data.get("source"), 
                                 route_class=data.get("route_class"),
                                 latency_ms=data.get("latency"),
                                 timestamp=data.get("ts"))
        else:
            raise ValueError(f"Unknown event type: {event_type}")
        
        
    def read(self) -> list[Events]:
        contents = []
        with open(self.path) as f:
            contents = [self.from_dict(json.loads(line)) for line in f]
        return contents