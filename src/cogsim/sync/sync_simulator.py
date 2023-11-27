from ..core.simulator import BaseSimulator
from ..core.user import BaseUser
from .sync_user import SyncUser

class SyncSimulator(BaseSimulator):
    def __init__(
        self,
        num_bands: int | None = None,
        users: list[SyncUser] | None = None,
        passes: int | None = None,
    ):
        """
        Initialize a simulator with a given number of bands and users.
        :param num_bands: The number of bands available to the users. Defaults to 10.
        :param users: A list of users meant to share the bands. Defaults to an empty list.
        """
        if users is None:
            users = []
        self.users: list[SyncUser] = users

        if num_bands is None:
            num_bands = 1
        self.num_bands = num_bands

        if passes is None:
            passes = 1
        self.passes = passes

        self.current_step = 0

    def step(self):
        """
        Perform a single synchronous step in the simulation. Each user will have an opportunity to
        evaluate the conditions of a band if they are currently occupying it, and switch bands or stop transmitting.
        """
        # Create a snapshot of the current bands.
        band_snapshot = self.band_contents()

        # Find the users in each band and run their logic
        for pass_index in range(self.passes):
            for user in self.users:
                user.step(
                    None
                    if user.current_band is None
                    else band_snapshot[user.current_band],
                    pass_index=pass_index,
                )

        # Once all users are done making decisions, calculate step metrics
        for user in self.users:
            user.calculate_step_metrics(self.current_step)

        self.current_step += 1

    def band_contents(self) -> list[list[SyncUser]]:
        """
        Splits the users within this simulation into their respective bands.
        :return: A list of lists of users. Each sublist represents a single band, and the User objects within
        that sublist are currently transmitting within that band.
        """
        band_contents: list[list[SyncUser]] = [[] for _ in range(self.num_bands)]
        for user in self.users:
            if user.current_band is not None:
                assert 0 <= user.current_band < self.num_bands
                band_contents[user.current_band].append(user)
        return band_contents