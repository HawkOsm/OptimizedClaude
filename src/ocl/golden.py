import json
from typing import Literal

from pydantic import BaseModel


class RouterCase(BaseModel):
    """
    Message model for OpenCL.
    """

    id: int
    session_active: bool
    message: str
    expected: Literal["TASK_NEW", "TRIVIAL", "PASSTHROUGH"]
    must_pass: bool | None = None
    note: str | None = None


class ClarifierCases(BaseModel):
    """
    Clarifier cases model for OpenCL.
    """

    id: int
    message: str
    context: str
    expect_questions_about: list[str]
    must_not_ask: list[str]


class Golden(BaseModel):
    """
    Golden model for OpenCL.
    """

    router_cases: list[RouterCase] = []
    clarifier_cases: list[ClarifierCases] = []

    def load_router_cases_from_json(self, json_data: str) -> None:
        """
        Load the model from a JSON string.
        """
        with open(json_data) as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    case_data = json.loads(line)
                    self.router_cases.append(RouterCase(**case_data))

    def load_clarifier_cases_from_json(self, json_data: str) -> None:
        """
        Load the model from a JSON string.
        """
        with open(json_data) as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    case_data = json.loads(line)
                    self.clarifier_cases.append(ClarifierCases(**case_data))
