from ..core.user import BaseUser
import numpy as np

__all__ = ["User2D"]

class User2D(BaseUser):
    x: float = 0.0
    y: float = 0.0

    def __init__(self, x: float, y: float):
        super().__init__()
        self.x = x
        self.y = y

    def distance_to(self, other_user: 'User2D'):
        return np.sqrt(np.power(self.x - other_user.x, 2) + np.power(self.y - other_user.y, 2))