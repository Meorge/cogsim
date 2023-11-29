from ...core.point2d import Point2D
from ..queue_user import QueueUser

__all__ = ["QueueUser2D"]


class QueueUser2D(QueueUser, Point2D):
    x: float = 0.0
    y: float = 0.0

    def __init__(
        self,
        wait_time: float | None = None,
        offset: float | None = None,
        x: float | None = None,
        y: float | None = None,
    ):
        super().__init__(wait_time, offset)
        self.x = x
        self.y = y
