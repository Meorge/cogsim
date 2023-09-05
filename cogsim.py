from abc import ABC, abstractmethod
from random import sample


class BaseUser(ABC):
    """
    The abstract base class for a simulated user in a cognitive radio simulation.
    Create a concrete subclass of this type and reimplement `make_decision_when_idle()` and `make_decision_when_in_band
    """
    current_band: int | None

    def __init__(self):
        self.current_band = None

    def switch_to_band(self, band_id: int | None):
        """
        Switch this user to a given band. Equivalent to setting `current_band_id` to `band_id`.
        Provided to increase readability.
        :param band_id: The ID of the band to switch to.
        """
        self.current_band = band_id

    @abstractmethod
    def make_decision(self, current_band_contents: list['BaseUser'] | None):
        """
        Evaluate the user's current situation, and move into or out of bands.
        :param current_band_contents: The other users in the band that this user is currently in. If this user
        is not currently in a band, the list will be `None`.
        """
        pass

    def calculate_step_metrics(self, current_step: int):
        """
        Evaluate the user's current situation after the latest step, and calculate any desired metrics.
        NOTE: Do not switch bands within this method.
        """
        pass


class Simulator:
    def __init__(self, num_bands: int | None = None, users: list[BaseUser] | None = None):
        """
        Initialize a simulator with a given number of bands and users.
        :param num_bands: The number of bands available to the users. Defaults to 10.
        :param users: A list of users meant to share the bands. Defaults to an empty list.
        """
        if users is None:
            users = []
        self.users: list[BaseUser] = users

        if num_bands is None:
            num_bands = 10
        self.num_bands = num_bands

        self.reset()

    def reset(self):
        self.current_step = 0

    def step(self):
        """
        Perform a single synchronous step in the simulation. Each user will have an opportunity to
        evaluate the conditions of a band if they are currently occupying it, and switch bands or stop transmitting.
        """
        # Create a snapshot of the current bands.
        band_snapshot = self.band_contents()

        # Find the users in each band and run their logic
        for user in self.users:
            user.make_decision(None if user.current_band is None else band_snapshot[user.current_band])

        # Once all users are done making decisions, calculate step metrics
        for user in self.users:
            user.calculate_step_metrics(self.current_step)

    def band_contents(self) -> list[list[BaseUser]]:
        """
        Splits the users within this simulation into their respective bands.
        :return: A list of lists of users. Each sublist represents a single band, and the User objects within
        that sublist are currently transmitting within that band.
        """
        band_contents: list[list[BaseUser]] = [[] for _ in range(self.num_bands)]
        for user in self.users:
            if user.current_band is not None:
                assert 0 <= user.current_band < self.num_bands
                band_contents[user.current_band].append(user)
        return band_contents
