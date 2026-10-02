from typing import Literal

from ocl.events.base import Events


class UserInput(Events):
    event: Literal["user_input"] = "user_input"
    text: str

