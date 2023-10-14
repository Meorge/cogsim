from json import dump
from time import time
from redisen_basic import User2D
from cogsim import BaseUser, Simulator
import numpy as np
from rich import print

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

rng = np.random.default_rng()


class RandomSwitchPrimaryUser(User2D):
    def __init__(
        self,
        x: float,
        y: float,
        time_in_range: tuple[int, int],
        time_out_range: tuple[int, int],
    ):
        super().__init__(x, y)
        self.time_in_range = time_in_range
        self.time_out_range = time_out_range
        self.timer = self.get_new_time_out_of_band()
        self.current_band = None

    def step(self, current_band_contents: list[BaseUser] | None, pass_index: int):
        if pass_index != 0:
            return

        self.timer -= 1
        if self.timer <= 0:
            if self.current_band is None:
                self.current_band = 0
                self.timer = self.get_new_time_in_band()
            else:
                self.current_band = None
                self.timer = self.get_new_time_out_of_band()

    def get_new_time_in_band(self):
        return rng.integers(self.time_in_range[0], self.time_in_range[1])

    def get_new_time_out_of_band(self):
        return rng.integers(self.time_out_range[0], self.time_out_range[1])


class ProbabilisticSecondaryUser(User2D):
    def __init__(self, x: float, y: float, attack_probability: float = 1.0):
        super().__init__(x, y)
        self.attack_probability = attack_probability
        self.current_band = 0
        self.reported_value = 0

    def step(self, current_band_contents: list[BaseUser] | None, pass_index: int):
        primary_users = [
            u for u in current_band_contents if isinstance(u, RandomSwitchPrimaryUser)
        ]

        if rng.uniform() <= self.attack_probability:
            """
            Give a dishonest reading of the primary user
            """
            self.reported_value = (
                NOISE_FLOOR if len(primary_users) > 0 else PU_TRANSMIT_POWER
            )
        else:
            """
            Give an honest reading of the primary user
            """
            if len(primary_users) > 0:
                pu = primary_users[0]
                distance_to_pu = self.distance_to(pu)
                power_loss = rng.normal(0.0, NORMAL_RNG_SIGMA)
                self.reported_value = (
                    pu.transmit_power
                    - 10 * PATH_LOSS_EXPONENT * np.log10(distance_to_pu)
                    - power_loss
                    - MULTI_PATH_FADING_EFFECT
                )
            else:
                self.reported_value = NOISE_FLOOR

def simulate(
    time_steps: int,
    attack_likelihood: float,
    time_in_range: tuple[int, int],
    time_out_range: tuple[int, int],
    su_area: tuple[float, float],
):
    su = ProbabilisticSecondaryUser(
        x=rng.uniform(high=su_area[0]),
        y=rng.uniform(high=su_area[1]),
        attack_probability=attack_likelihood,
    )
    pu = RandomSwitchPrimaryUser(
        x=rng.uniform(high=su_area[0]),
        y=rng.uniform(high=su_area[1]),
        time_in_range=time_in_range,
        time_out_range=time_out_range,
    )

    user_list = [su, pu]

    sim = Simulator(num_bands=1, users=user_list, passes=1)

    history = []
    for _ in range(time_steps):
        sim.step()
        history.append([su.reported_value, 1 if pu.current_band is not None else 0])

    result = {
        "config": {
            "su_area_width": su_area[0],
            "su_area_height": su_area[1],
            "time_in_range": {"low": time_in_range[0], "high": time_in_range[1]},
            "time_out_range": {"low": time_out_range[0], "high": time_out_range[1]},
        },
        "inputs": history,
        "output": attack_likelihood,
    }

    return result

def main():
    time_steps = 10000

    su_area = (1000.0, 1000.0)

    time_in_range = (100, 200)
    time_out_range = (50, 100)

    for i in range(11):
        attack_likelihood = i / 10
        sim_result = simulate(
            time_steps=time_steps,
            attack_likelihood=attack_likelihood,
            time_in_range=time_in_range,
            time_out_range=time_out_range,

            su_area=su_area,
        )

        with open(f'train-{attack_likelihood}.json', 'w') as f:
            dump(sim_result, f, indent=4)


if __name__ == "__main__":
    main()
