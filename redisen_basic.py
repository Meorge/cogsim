"""
An implementation of basic ReDiSen using the cogsim library.
"""
from cogsim import BaseUser, Simulator
import numpy as np

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


def primary_users_in_band(
    current_band_contents: list["BaseUser"],
) -> list["PrimaryUser"]:
    if current_band_contents is None:
        return []
    return [u for u in current_band_contents if isinstance(u, PrimaryUser)]

def calculate_reputations(
    neighbor_values: dict["User2D", float]
) -> dict["User2D", float]:
    """
    Calculates the ReDiSen reputation scores for each neighbor
    """
    # Defined as V-tilde in the literature
    avg_neighbors = np.average([v for v in neighbor_values.values()])

    denominator = np.sum([np.abs(v - avg_neighbors) for v in neighbor_values.values()])

    frac_part = len(neighbor_values) / denominator

    output: dict["User2D", float] = {
        neighbor: 2 - frac_part * np.abs(neighbor_value - avg_neighbors)
        for neighbor, neighbor_value in neighbor_values.items()
    }
    return output


class User2D(BaseUser):
    x: float = 0.0
    y: float = 0.0
    transmit_power: float = 4.0  # measured in watts

    def __init__(self, x: float, y: float):
        super().__init__()
        self.x = x
        self.y = y

    def distance_to(self, other_user: 'User2D'):
        return np.sqrt(np.power(self.x - other_user.x, 2) + np.power(self.y - other_user.y, 2))


class PrimaryUser(User2D):
    def __init__(self, x: float, y: float, transmit: bool):
        super().__init__(x, y)
        self.transmit = transmit
        if self.transmit:
            self.switch_to_band(0)
        else:
            self.switch_to_band(None)

class SecondaryUser(User2D):
    """
    A user who uses cooperative spectrum sensing.
    """

    other_user_votes: dict["SecondaryUser", float]
    sensed_pu_history: list[float]
    last_sensed_pu_value: float

    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        self.other_user_votes = {}
        self.sensed_pu_history = []
        self.last_sensed_pu_value = 0.0

        # For basic ReDiSen, everyone will need to be in the same band
        self.switch_to_band(0)

    def sense_pu_value(self, current_band_contents: list["BaseUser"]) -> float:
        """
        Honestly senses for the presence of a primary user.
        :param current_band_contents: The list of users in this user's current band.
        :return: The primary user sensed value.
        """
        primary_users = primary_users_in_band(current_band_contents)
        if len(primary_users) > 0:
            pu = primary_users[
                0
            ]  # For now, we'll just use the first primary user found
            distance = self.distance_to(pu)
            power_loss = np.random.default_rng().normal(0.0, NORMAL_RNG_SIGMA)
            return (
                pu.transmit_power
                - 10 * PATH_LOSS_EXPONENT * np.log10(distance)
                - power_loss
                - MULTI_PATH_FADING_EFFECT
            )
        else:
            return NOISE_FLOOR


class BasicReDiSenSecondaryUser(SecondaryUser):
    def step(self, current_band_contents: list[BaseUser] | None, pass_index: int):
        if pass_index == 0:
            self.measure_and_send_to_neighbors(current_band_contents)
        elif pass_index == 1:
            self.evaluate_neighbors()

    def measure_and_send_to_neighbors(self, band: list[BaseUser] | None):
        sensed_pu_value = self.sense_pu_value(band)
        for user in band:
            if isinstance(user, BasicReDiSenSecondaryUser):
                user.receive_primary_user_readings(self, sensed_pu_value)
                
    def evaluate_neighbors(self):
        reputations = calculate_reputations(self.other_user_votes) if USE_REDISEN else {u: 1.0 for u in self.other_user_votes.keys()}

        self.sensed_pu_history: list[float] = []
        final_pu_value = self.other_user_votes[self]

        for _ in range(150):
            summation = 0.0
            for neighbor in reputations.keys():
                summation += (1 - DISCOUNT_FACTOR) * reputations[
                    neighbor
                ] * (self.other_user_votes[neighbor] - final_pu_value)

            final_pu_value += summation

            # Capture PU value here (inside this loop) for comparing to ReDiSen
            self.sensed_pu_history.append(final_pu_value)

        # Once we get here, we have the ReDiSen estimate of the PU's energy.
        # Then we can choose what to do about it (such as leaving the band).

    def receive_primary_user_readings(self, source: "BasicReDiSenSecondaryUser", value: float):
        self.other_user_votes[source] = value

class MaliciousSecondaryUser(BasicReDiSenSecondaryUser):
    def __init__(self, x: float, y: float, attack_likelihood: float = 1.0):
        super().__init__(x, y)
        self.attack_likelihood = attack_likelihood

    def step(self, current_band_contents: list[BaseUser] | None, pass_index: int):
        """
        Malicious secondary users aren't concerned with evaluating their
        neighbors for now, so they only need behavior for the first pass.
        """
        if pass_index == 0:
            self.measure_and_send_to_neighbors(current_band_contents)

    def sense_pu_value(self, current_band_contents: list["BaseUser"]) -> float:
        """
        Malicious secondary users will decide whether to give accurate results
        or not depending on the probability assigned to them.
        """
        if np.random.default_rng().uniform() < self.attack_likelihood:
            return (
                NOISE_FLOOR
                if len(primary_users_in_band(current_band_contents)) > 0
                else PU_TRANSMIT_POWER
            )
        else:
            super().sense_pu_value(current_band_contents)

PU_TRANSMIT = True
USE_REDISEN = True

def main():
    user_list = [
        SecondaryUser(
            x=np.random.default_rng().uniform(high=SU_AREA_WIDTH),
            y=np.random.default_rng().uniform(high=SU_AREA_HEIGHT),
        )
        for _ in range(7)
    ]

    user_list.extend([
        MaliciousSecondaryUser(
            x=np.random.default_rng().uniform(high=SU_AREA_WIDTH),
            y=np.random.default_rng().uniform(high=SU_AREA_HEIGHT),
        )
        for _ in range(3)
    ])

    user_list.append(
        PrimaryUser(
            x=np.random.default_rng().uniform(high=SU_AREA_WIDTH),
            y=np.random.default_rng().uniform(high=SU_AREA_HEIGHT),
            transmit=PU_TRANSMIT
        )
    )

    sim = Simulator(num_bands=1, users=user_list, passes=2)

    for _ in range(1):
        sim.step()

    # Now that we're done, let's check where the benign nodes ended
    if PU_TRANSMIT:
        print("PU was transmitting (higher value more accurate - malicious users trying to drag it down)")
    else:
        print("PU was not transmitting (lower value more accurate - malicious users trying to raise it up)")
    for i, user in enumerate(user_list):
        if isinstance(user, SecondaryUser) and not isinstance(user, MaliciousSecondaryUser):
            print(f"{i} - started at {user.sensed_pu_history[0]}, ended at {user.sensed_pu_history[-1]}")



if __name__ == "__main__":
    main()
