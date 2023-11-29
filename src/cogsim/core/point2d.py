from abc import ABC
import numpy as np

__all__ = ["Point2D"]

class Point2D(ABC):
    x: float = 0.0
    y: float = 0.0
    
    def distance_to(self, other: "Point2D"):
        return np.sqrt(np.power(self.x - other.x, 2) + np.power(self.y - other.y, 2))
