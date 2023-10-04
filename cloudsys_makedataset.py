from redisen_basic import (
    SU_AREA_WIDTH,
    SU_AREA_HEIGHT,
    User2D,
)
from cogsim import BaseUser, Simulator
import numpy as np
from rich import print

TIME_IN_BAND = 100
TIME_OUT_OF_BAND = 50

# The transmission power of the PU.
# Units of dB m.
PU_TRANSMIT_POWER: float = 80.0

# The multi-path fading effect.
# Units of dB m?
MULTI_PATH_FADING_EFFECT: float = 0.0

# What honest nodes should report when they do not detect the PU,
# or what malicious nodes should report when they do detect the PU.
# Units of dB m.
NOISE_FLOOR: float = -111.0

# Represented as sigma (σ) in paper.
# Used for calculating the power loss effect.
# Units of dB m.
NORMAL_RNG_SIGMA: float = 3.0

# Represented as alpha (ɑ) in paper.
# Described as "path-loss exponent", but value is not given.
# Online searches suggest a value of 2.0 is good for "free space",
# but a value of 1.0 makes the results line up with the ReDiSen paper the most.
PATH_LOSS_EXPONENT: float = 1.0

class RandomSwitchPrimaryUser(User2D):
    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        self.timer = TIME_OUT_OF_BAND
        self.current_band = None

    def step(self, current_band_contents: list[BaseUser] | None, pass_index: int):
        if pass_index != 0:
            return
        
        self.timer -= 1
        if self.timer <= 0:
            if self.current_band is None:
                self.current_band = 0
                self.timer = TIME_IN_BAND
            else:
                self.current_band = None
                self.timer = TIME_OUT_OF_BAND

class ProbabilisticSecondaryUser(User2D):
    def __init__(self, x: float, y: float, attack_probability: float = 1.0):
        super().__init__(x, y)
        self.attack_probability = attack_probability
        self.current_band = 0
        self.reported_value = 0

    def step(self, current_band_contents: list[BaseUser] | None, pass_index: int):
        primary_users = [u for u in current_band_contents if isinstance(u, RandomSwitchPrimaryUser)]

        if np.random.default_rng().uniform() <= self.attack_probability:
            """
            Give a dishonest reading of the primary user
            """
            self.reported_value = (
                NOISE_FLOOR
                if len(primary_users) > 0
                else PU_TRANSMIT_POWER
            )
        else:
            """
            Give an honest reading of the primary user
            """
            if len(primary_users) > 0:
                pu = primary_users[0]
                distance_to_pu = self.distance_to(pu)
                power_loss = np.random.default_rng().normal(0.0, NORMAL_RNG_SIGMA)
                self.reported_value = (
                    pu.transmit_power
                    - 10 * PATH_LOSS_EXPONENT * np.log10(distance_to_pu)
                    - power_loss
                    - MULTI_PATH_FADING_EFFECT
                )
            else:
                self.reported_value = NOISE_FLOOR
    


def main():
    attack_likelihood = 0.4

    su = ProbabilisticSecondaryUser(
        x=np.random.default_rng().uniform(high=SU_AREA_WIDTH),
        y=np.random.default_rng().uniform(high=SU_AREA_HEIGHT),
        attack_probability=attack_likelihood,
    )
    pu = RandomSwitchPrimaryUser(
        x=np.random.default_rng().uniform(high=SU_AREA_WIDTH),
        y=np.random.default_rng().uniform(high=SU_AREA_HEIGHT),
    )

    user_list = [su, pu]

    sim = Simulator(num_bands=1, users=user_list, passes=1)

    history = []
    for _ in range(1000):
        sim.step()
        history.append(((su.reported_value, 1 if pu.current_band is not None else 0), attack_likelihood))

    print(history)

if __name__ == "__main__":
    main()
