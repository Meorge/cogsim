from cogsim import BaseUser, Simulator
from random import randint
from math import log
import numpy as np

# TODO: Set number of bands to 1, maybe number of users to 10 for now.
#  For initial tests, we should have the PU just either transmit or not transmit the whole time.
#  Once that's working and we can get data out of it, we can try having it switch between transmitting and not,
#  and see how quickly the SUs can detect it.

CONGESTION_LIMIT = 3
NUM_BANDS = 10
NUM_USERS = 30
TOTAL_STEPS = 100

# Represented as lambda (λ) in paper. No units.
DISCOUNT_FACTOR: float = 0.995

# What honest nodes should report when they do not detect the PU,
# or what malicious nodes should report when they do detect the PU.
# Units of dB m.
NOISE_FLOOR: float = -111.0

# The transmission power of the PU.
# Units of dB m.
PU_TRANSMIT_POWER: float = 80.0

# The multi-path fading effect.
# Units of dB m?
MULTI_PATH_FADING_EFFECT: float = 0.0

# Represented as sigma (σ) in paper.
# Used for calculating the power loss effect.
# Units of dB m.
NORMAL_RNG_SIGMA: float = 3.0

# Represented as alpha (ɑ) in paper.
# Described as "path-loss exponent", but value is not given.
# Online searches suggest a value of 2.0 is good for "free space",
# but a value of 1.0 makes the results line up with the ReDiSen paper the most.
PATH_LOSS_EXPONENT: float = 1.0

# Height and width of the area in which SUs may be placed.
# Units of m.
SU_AREA_WIDTH: float = 1000.0
SU_AREA_HEIGHT: float = 1000.0


def primary_users_in_band(current_band_contents: list['BaseUser']) -> list['PrimaryUser']:
    if current_band_contents is None: return []
    return [u for u in current_band_contents if isinstance(u, PrimaryUser)]


def distance_between_users(a: 'User', b: 'User') -> float:
    return np.sqrt(np.power(a.x - b.x, 2) + np.power(a.y - b.y, 2))


class User(BaseUser):
    x: float = 0.0
    y: float = 0.0
    transmit_power: float = 4.0  # measured in watts

    def __init__(self, x: float, y: float):
        super().__init__()
        self.x = x
        self.y = y


class PrimaryUser(User):
    def __init__(self, x: float, y: float, licensed_band: int = 0):
        super().__init__(x, y)
        self.licensed_band = licensed_band
        self.time_left_transmitting = 0
        self.time_left_waiting = 0

    def step(self, current_band_contents: list['BaseUser'] | None, pass_index: int):
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


class SimpleUser(BaseUser):
    time_spent_transmitting: int = 0
    transmit_power: float = 4.0  # measured in watts
    current_band_contents: list['BaseUser']

    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        self.time_spent_transmitting = 0
        self.current_band_contents = []

    def step(self, current_band_contents: list['BaseUser'] | None, pass_index: int):
        self.current_band_contents = current_band_contents
        # Currently in a band, so decide whether to stay here or leave
        if self.current_band is not None:
            # Switch to another band if there are too many users
            if len(current_band_contents) > CONGESTION_LIMIT:
                self.switch_to_band(None)

            # Switch to another band if the primary user is in this band
            if len(primary_users_in_band(current_band_contents)) > 0:
                self.switch_to_band(None)

        # Not currently in a band, so choose a band to join
        else:
            new_band = randint(0, NUM_BANDS - 1)
            self.switch_to_band(new_band)

    def calculate_step_metrics(self, current_step: int):
        if self.current_band is not None:
            self.time_spent_transmitting += 1

    def calculate_transmission_rate(self, current_band_contents: list['User']):
        channel_bandwidth = 20.0  # B, measured in MHz (should this be changed to Hz??)
        channel_gain = 10.0  # G_s
        channel_gain_between_me_and_other_su = 5.0  # G_si
        additive_white_gaussian_noise = 0.05  # W, measured in watts

        # Calculate summation at bottom
        denominator = 0.0
        for other_user in current_band_contents:
            transmit_power_of_other_su = other_user.transmit_power
            denominator += channel_gain_between_me_and_other_su * transmit_power_of_other_su + additive_white_gaussian_noise

        # Calculate numerator
        numerator = channel_gain * self.transmit_power

        # Calculate remaining
        divided = numerator / denominator
        result = channel_bandwidth * log(1 + divided)
        return result


class CSSUser(User):
    """
    A user who uses cooperative spectrum sensing. They will attempt to detect the presence of
    a primary user in their current band, and send the result to their neighbors (i.e., other users in their band).
    """
    other_user_votes: dict['CSSUser', float]
    sensed_pu_history: list[float]
    last_sensed_pu_value: float

    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        self.other_user_votes = {}
        self.sensed_pu_history = []
        self.last_sensed_pu_value = 0.0

    def receive_primary_user_presence_vote(self, source_user: 'CSSUser', pu_value: float):
        self.other_user_votes[source_user] = pu_value

    def sense_pu_value(self, current_band_contents: list['BaseUser']) -> float:
        """
        Honestly senses for the presence of a primary user.
        :param current_band_contents: The list of users in this user's current band.
        :return: The primary user sensed value.
        """
        primary_users = primary_users_in_band(current_band_contents)
        if len(primary_users) > 0:
            pu = primary_users[0]  # For now, we'll just use the first primary user found
            distance = distance_between_users(self, pu)
            power_loss = np.random.default_rng().normal(0.0, NORMAL_RNG_SIGMA)
            return pu.transmit_power - 10 * PATH_LOSS_EXPONENT * np.log10(
                distance) - power_loss - MULTI_PATH_FADING_EFFECT
        else:
            return NOISE_FLOOR

    def step(self, current_band_contents: list['BaseUser'] | None, pass_index: int):
        """
        Sense the primary user's presence or absence. Malicious nodes will override this method to provide faulty
        results.
        :param current_band_contents:
        :return:
        """

        # If the user is not currently transmitting in a band, then they should choose a band to transmit in
        if current_band_contents is None:
            self.switch_to_band(randint(0, NUM_BANDS - 1))
            return

        sensed_pu_value = self.sense_pu_value(current_band_contents)
        for user in current_band_contents:
            if isinstance(user, CSSUser) and user != self:
                user.receive_primary_user_presence_vote(self, sensed_pu_value)

        # Calculate average measured value from neighbors
        neighbors_with_submitted_values = [u for u in current_band_contents if u in self.other_user_votes]

        # Only attempt ReDiSen algorithm if we have neighbor data to use
        if len(neighbors_with_submitted_values) != 0:
            avg_neighbors = np.sum([self.other_user_votes[u] for u in neighbors_with_submitted_values]) / len(neighbors_with_submitted_values)

            # Compute denominator summation (same for all reputation calculation for all users)
            denominator_summation = np.sum(
                [np.abs(self.other_user_votes[u] - avg_neighbors) for u in neighbors_with_submitted_values])
            if denominator_summation == 0.0:
                denominator_summation = 1.0

            # Calculate reputation for each user
            reputations = {}
            for other_user in neighbors_with_submitted_values:
                if other_user not in self.other_user_votes:
                    continue
                numerator = len(neighbors_with_submitted_values) * np.abs(self.other_user_votes[other_user] - avg_neighbors)
                reputations[other_user] = 2 - numerator / denominator_summation

            # Start with our current value, then modify it over update sessions to reflect the contributions from neighbors
            for i in range(150):
                summation = 0.0
                for other_user in neighbors_with_submitted_values:
                    summation += (1 - DISCOUNT_FACTOR) * reputations[other_user] * (
                                self.other_user_votes[other_user] - sensed_pu_value)
                sensed_pu_value += summation

        self.last_sensed_pu_value = sensed_pu_value

        # Now we have a reputation-based sense value.
        # If the value is positive, then we assume the PU is present, and vacate the band.
        # Otherwise, we assume the PU is absent, and thus that we can remain here without disrupting PU service.
        pu_is_present = sensed_pu_value >= 0.0
        if pu_is_present:
            self.switch_to_band(None)
        else:
            pass

    def calulcate_step_metrics(self, current_step: int):
        """
        Return the calculated PU presence value
        :param current_step:
        :return:
        """
        self.sensed_pu_history.append(self.last_sensed_pu_value)

class MaliciousCSSUser(CSSUser):
    def sense_pu_value(self, current_band_contents: list['BaseUser']) -> float:
        return NOISE_FLOOR if len(primary_users_in_band(current_band_contents)) > 0 else PU_TRANSMIT_POWER


def main():
    user_list = [CSSUser(x=np.random.default_rng().uniform(high=SU_AREA_WIDTH),
                         y=np.random.default_rng().uniform(high=SU_AREA_HEIGHT)) for _ in range(NUM_USERS)]
    user_list.append(MaliciousCSSUser(x=np.random.default_rng().uniform(high=SU_AREA_WIDTH),
                                      y=np.random.default_rng().uniform(high=SU_AREA_HEIGHT)))
    user_list.append(PrimaryUser(x=np.random.default_rng().uniform(high=SU_AREA_WIDTH),
                                 y=np.random.default_rng().uniform(high=SU_AREA_HEIGHT)))
    sim = Simulator(num_bands=NUM_BANDS, users=user_list, passes=2)

    for step in range(TOTAL_STEPS):
        sim.step()

    # Done with simulation, let's see how often each node got to transmit
    for i, user in enumerate(user_list):
        if isinstance(user, CSSUser) and not isinstance(user, MaliciousCSSUser):
            ...  # TODO: get some stats!


if __name__ == '__main__':
    main()
