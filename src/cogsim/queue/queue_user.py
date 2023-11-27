from ..core.user import BaseUser

__all__ = ["QueueUser"]

class QueueUser(BaseUser):
    wait_time: float = 1.0
    wait_time_remaining: float = 0.0

    def __init__(self, wait_time: float | None = None):
        super().__init__()
        if wait_time is None:
            wait_time = 1.0
        self.wait_time = wait_time

    def reset_wait_time(self):
        self.wait_time_remaining = self.wait_time

    def deduct_wait_time(self, amount: float):
        self.wait_time_remaining -= amount