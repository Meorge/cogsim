from abc import ABC

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

    def step(
        self, current_band_contents: list["BaseUser"] | None, pass_index: int
    ):
        """
        Evaluate the user's current situation, and move into or out of bands.
        :param current_band_contents: The other users in the band that this user is currently in. If this user
        is not currently in a band, the list will be `None`.
        :param pass_index: The index of the current pass for this step. All users will run their step function
        with a given pass index; after that, they will all run again with the next pass index, or stop if the
        total number of passes in the Simulator has been fulfilled.
        """
        pass

    def calculate_step_metrics(self, current_step: int):
        """
        Evaluate the user's current situation after the latest step, and calculate any desired metrics.
        NOTE: Do not switch bands within this method.
        """
        pass