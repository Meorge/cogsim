# This is a sample Python script.

# Press ⌃F5 to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from cogsim import BaseUser, Simulator
from random import randint


CONGESTION_LIMIT = 3
NUM_BANDS = 10
NUM_USERS = 30
TOTAL_STEPS = 1000

class User(BaseUser):
    time_spent_transmitting = 0
    def __init__(self):
        super().__init__()
        self.time_spent_transmitting = 0

    def make_decision(self, current_band_contents: list['BaseUser'] | None):
        # Currently in a band, so decide whether to stay here or leave
        if self.current_band is not None:
            number_of_users_in_band = len(current_band_contents)
            if number_of_users_in_band > CONGESTION_LIMIT:
                # If we've gotten here, then the congestion limit for this band
                # has been exceeded and we need to pull out
                self.switch_to_band(None)

        # Not currently in a band, so choose a band to join
        else:
            new_band = randint(0, NUM_BANDS - 1)
            self.switch_to_band(new_band)

    def calculate_step_metrics(self, current_step: int):
        if self.current_band is not None:
            self.time_spent_transmitting += 1


def main():
    user_list = [User() for _ in range(NUM_USERS)]
    sim = Simulator(num_bands=NUM_BANDS, users=user_list)

    for _ in range(TOTAL_STEPS):
        sim.step()

    # Done with simulation, let's see how often each node got to transmit
    for i, node in enumerate(user_list):
        print(f"{i}: {node.time_spent_transmitting * 100.0 / TOTAL_STEPS:.2f}%")


if __name__ == '__main__':
    main()

