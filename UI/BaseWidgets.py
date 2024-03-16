# -*- coding: utf-8 -*-
# cython: language_level = 3

from collections import deque
from dataclasses import dataclass
from enum import Enum
from math import cos
from math import pi
from typing import Optional
from typing import override

from PyQt5.QtCore import QDateTime
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QRectF
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QPainterPath
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from .tools import showException


class GetScale(QWidget):
    scaleChanged = pyqtSignal(float, float, name="scaleChange")

    def __init__(self, parent=None, reference_size: QSize = None):
        super().__init__(parent)
        self.scaleWidth = 1.0
        self.scaleHeight = 1.0
        if reference_size is None:
            try:
                reference_size = self.parent().minimumSize()
            except AttributeError:
                reference_size = self.minimumSize()
        self.reference_size = reference_size

        # noinspection PyUnresolvedReferences
        self.scaleChanged.connect(self.autoResize)

    @showException
    @override
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        size = self.reference_size
        try:
            self.scaleWidth = event.size().width() / size.width()
        except ZeroDivisionError:
            pass
        try:
            self.scaleHeight = event.size().height() / size.height()
        except ZeroDivisionError:
            pass
        # noinspection PyUnresolvedReferences
        self.scaleChanged.emit(self.scaleWidth, self.scaleHeight)

    def autoResize(self, scale_width: float, scale_height: float) -> None:
        """
        自动调整窗口大小
        :param scale_width: 窗口宽度比例
        :param scale_height: 窗口高度比例
        :return: None
        """


@dataclass
class Radius:
    xRadius: int
    yRadius: int


class RoundShadow(QWidget):
    """圆角边框类"""

    @showException
    def __init__(
            self,
            parent=None,
            /, *,
            radius: Optional[Radius] = None,
            background_color: Optional[QColor] = None,
            draw_shadow: bool = False,
            translucent_background: bool = False
    ):
        super().__init__(parent)
        self.border_width = 8
        self.draw_shadow = draw_shadow
        self.shadow_color = QColor(192, 192, 192, 50)

        if radius is None:
            radius = Radius(xRadius=4, yRadius=4)
        if background_color is None:
            background_color = Qt.white
        self.background_color = background_color

        self.radius = radius
        self.background_rect = self.rect()

        if translucent_background:
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

    def shadow(self):
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)

        pat = QPainter(self)
        pat.setRenderHint(pat.Antialiasing)
        pat.fillPath(path, QBrush(Qt.white))

        color = self.shadow_color

        for i in range(10):
            i_path = QPainterPath()
            i_path.setFillRule(Qt.WindingFill)
            t = 10 - i
            ref = QRectF(t, t, self.width() - t * 2, self.height() - t * 2)
            i_path.addRoundedRect(ref, self.border_width, self.border_width)
            color.setAlpha(int(150 - i ** 0.5 * 50))
            pat.setPen(color)
            pat.drawPath(i_path)

    def fillet(self):
        # 圆角
        pat2 = QPainter(self)
        pat2.setRenderHint(pat2.Antialiasing)  # 抗锯齿
        pat2.setBrush(self.background_color)
        pat2.setPen(Qt.transparent)

        rect = self.background_rect
        rect.setLeft(rect.left())
        rect.setTop(rect.top())
        rect.setWidth(rect.width())
        rect.setHeight(rect.height())
        pat2.drawRoundedRect(rect, self.radius.xRadius, self.radius.yRadius)

    @showException
    @override
    def paintEvent(self, *args):
        if self.draw_shadow:
            self.shadow()
        self.fillet()


class SmoothlyScrollArea(QScrollArea):
    """ A scroll area which can scroll smoothly """

    @showException
    def __init__(self, parent=None, orient=Qt.Vertical):
        """
        Parameters
        ----------
        parent: QWidget
            parent widget

        orient: Orientation
            scroll orientation
        """
        super().__init__(parent)
        self.orient = orient
        self.fps: int = 60
        self.duration: int = 400
        self.stepsTotal: int = 0
        self.stepRatio: float = 4
        self.acceleration: float = 1
        self.lastWheelEvent: Optional[QWheelEvent] = None
        self.scrollStamps: deque = deque()
        self.stepsLeftQueue: deque = deque()
        self.smoothMoveTimer: QTimer = QTimer(self)
        self.smoothMode: SmoothMode = SmoothMode(SmoothMode.LINEAR)
        # noinspection PyUnresolvedReferences
        self.smoothMoveTimer.timeout.connect(self._smoothMove)

    @showException
    def setSmoothMode(self, smooth_mode):
        """ set smooth mode """
        self.smoothMode = smooth_mode

    @showException
    @override
    def wheelEvent(self, e):
        if self.smoothMode == SmoothMode.NO_SMOOTH:
            super().wheelEvent(e)
            return

        now = QDateTime.currentDateTime().toMSecsSinceEpoch()
        self.scrollStamps.append(now)
        while now - self.scrollStamps[0] > 500:
            self.scrollStamps.popleft()

        acceleration_ratio = min(len(self.scrollStamps) / 15, 1)
        if not self.lastWheelEvent:
            self.lastWheelEvent = QWheelEvent(e)
        else:
            self.lastWheelEvent = e

        self.stepsTotal = self.fps * self.duration / 1000

        delta = e.angleDelta().y() * self.stepRatio
        if self.acceleration > 0:
            delta += delta * self.acceleration * acceleration_ratio

        self.stepsLeftQueue.append([delta, self.stepsTotal])

        self.smoothMoveTimer.start(int(1000 / self.fps))

    @showException
    def _smoothMove(self):
        """ scroll smoothly when timer time out """
        total_delta = 0

        for i in self.stepsLeftQueue:
            total_delta += self._subDelta(i[0], i[1])
            i[1] -= 1

        while self.stepsLeftQueue and self.stepsLeftQueue[0][1] == 0:
            self.stepsLeftQueue.popleft()

        if self.orient == Qt.Vertical:
            p = QPoint(0, round(total_delta))
            bar = self.verticalScrollBar()
        else:
            p = QPoint(round(total_delta), 0)
            bar = self.horizontalScrollBar()

        e = QWheelEvent(
            self.lastWheelEvent.pos(),
            self.lastWheelEvent.globalPos(),
            QPoint(),
            p,
            round(total_delta),
            self.orient,
            self.lastWheelEvent.buttons(),
            Qt.NoModifier
        )

        QApplication.sendEvent(bar, e)

        if not self.stepsLeftQueue:
            self.smoothMoveTimer.stop()

    @showException
    def _subDelta(self, delta, steps_left):
        """ get the interpolation for each step """
        m = self.stepsTotal / 2
        x = abs(self.stepsTotal - steps_left - m)

        res = 0
        if self.smoothMode == SmoothMode.NO_SMOOTH:
            res = 0
        elif self.smoothMode == SmoothMode.CONSTANT:
            res = delta / self.stepsTotal
        elif self.smoothMode == SmoothMode.LINEAR:
            res = 2 * delta / self.stepsTotal * (m - x) / m
        elif self.smoothMode == SmoothMode.QUADRATIC:
            res = 3 / 4 / m * (1 - x * x / m / m) * delta
        elif self.smoothMode == SmoothMode.COSINE:
            res = (cos(x * pi / m) + 1) / (2 * m) * delta

        return res


class SmoothMode(Enum):
    """ Smooth mode """
    NO_SMOOTH = 0
    CONSTANT = 1
    LINEAR = 2
    QUADRATIC = 3
    COSINE = 4


class MatplotlibWidget(QWidget):

    def __init__(self, parent=None):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        super().__init__(parent)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)


__all__ = ("SmoothlyScrollArea", "SmoothMode", "RoundShadow", "GetScale", "MatplotlibWidget")
