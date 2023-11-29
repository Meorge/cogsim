from ..core.simulator import BaseSimulator
from .queue_user import QueueUser


class QueueSimulator(BaseSimulator):
    def __init__(
        self, num_bands: int | None = None, users: list[QueueUser] | None = None
    ):
        if users is None:
            users = []
        self.users: list[QueueUser] = users

        if num_bands is None:
            num_bands = 1
        self.num_bands = num_bands

        self.total_time = 0

    def step(self):
        # Find the user with the lowest time remaining
        next_user: QueueUser
        time_to_deduct: float
        next_user, time_to_deduct = min(
            [(u, u.wait_time_remaining) for u in self.users], key=lambda v: v[1]
        )

        # Deduct this amount of time from everyone
        for user in self.users:
            if user == next_user:
                user.reset_wait_time()
            else:
                user.deduct_wait_time(time_to_deduct)

        next_user.step()

        self.total_time += time_to_deduct
