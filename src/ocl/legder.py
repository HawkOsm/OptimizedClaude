import json
from datetime import datetime


class UserInput:
    def __init__(self, text: str):
        self.text = text
        self.timestamp = datetime.now().isoformat()
        self.session_id = None  # Placeholder for session ID, can be set later if needed

    def json(self):
        return {"v": 1, "ts": self.timestamp,"session_id": self.session_id, "event": "user_input", "text": self.text}

class Ledger:
    def __init__(self, path: str):
        self.path = path

    def emit(self, user_input: UserInput):
        user_input_json = user_input.json()
        with open(self.path, 'a') as f:
            f.write(json.dumps(user_input_json) + '\n')

    def read(self):
        contents = []
        with open(self.path) as f:
            contents = [UserInput(json.loads(line)['text']) for line in f]
        return contents