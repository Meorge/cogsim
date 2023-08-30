from cogsim import BaseUser, Simulator
from random import randint

CONGESTION_LIMIT = 3
NUM_BANDS = 10
NUM_USERS = 30
TOTAL_STEPS = 100000


def primary_user_in_band(current_band_contents: list['BaseUser']):
    return any([isinstance(user, PrimaryUser) for user in current_band_contents])


class PrimaryUser(BaseUser):
    def __init__(self, licensed_band: int = 0):
        super().__init__()
        self.licensed_band = licensed_band
        self.time_left_transmitting = 0
        self.time_left_waiting = 0

    def make_decision(self, current_band_contents: list['BaseUser'] | None):
        if self.current_band is not None:
            self.time_left_transmitting -= 1
            if self.time_left_transmitting <= 0:
                self.current_band = None
                self.time_left_waiting = randint(10, 15)
        else:
            self.time_left_waiting -= 1
            if self.time_left_waiting <= 0:
                self.current_band = self.licensed_band
                self.time_left_transmitting = randint(5, 10)

    def calculate_step_metrics(self, current_step: int):
        pass


class User(BaseUser):
    time_spent_transmitting = 0

    def __init__(self):
        super().__init__()
        self.time_spent_transmitting = 0

    def make_decision(self, current_band_contents: list['BaseUser'] | None):
        # Currently in a band, so decide whether to stay here or leave
        if self.current_band is not None:
            # Switch to another band if there are too many users
            if len(current_band_contents) > CONGESTION_LIMIT:
                self.switch_to_band(None)

            # Switch to another band if the primary user is in this band
            if primary_user_in_band(current_band_contents):
                self.switch_to_band(None)

        # Not currently in a band, so choose a band to join
        else:
            new_band = randint(0, NUM_BANDS - 1)
            self.switch_to_band(new_band)

    def calculate_step_metrics(self, current_step: int):
        if self.current_band is not None:
            self.time_spent_transmitting += 1

# TODO: Utility function
# We often look at convergence time after primary user disruption


def main():
    user_list = [User() for _ in range(NUM_USERS)]
    user_list.append(PrimaryUser())
    sim = Simulator(num_bands=NUM_BANDS, users=user_list)

    for _ in range(TOTAL_STEPS):
        sim.step()

    # Done with simulation, let's see how often each node got to transmit
    for i, node in enumerate(user_list):
        if isinstance(node, User):
            print(f"{i}: {node.time_spent_transmitting * 100.0 / TOTAL_STEPS:.2f}%")


if __name__ == '__main__':
    main()
