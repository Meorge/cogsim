from .user import BaseUser
from abc import ABC

class BaseSimulator(ABC):
    def __init__(
        self,
        users: list[BaseUser] | None = None,
    ):
        ...

    def step(self):
        ...
