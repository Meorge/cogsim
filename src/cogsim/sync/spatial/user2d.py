from ...core.point2d import Point2D
from ..sync_user import SyncUser

__all__ = ["User2D"]

class User2D(SyncUser, Point2D):
    x: float = 0.0
    y: float = 0.0

    def __init__(self, x: float | None = None, y: float | None = None):
        super().__init__()
        self.x = x
        self.y = y