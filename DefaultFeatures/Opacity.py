# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.2Dev"
__description__ = "Adjustable window transparency"

import time
import uuid
from typing import override

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMenu

from UI.ABC import AbcMenu
from UI.RegisterUI import register_menu
from UI.tools import showException


@register_menu
class OpacityMenu(AbcMenu):
    def __init__(self, _menubar, _window):
        super().__init__(_menubar, _window)
        self.menu: QMenu | None = None
        self.animationRunning = None

    @showException
    def _gradient(self, to):
        this_animation = uuid.uuid4()
        self.animationRunning = this_animation

        _from = self.window.windowOpacity()
        # 从_from渐变到to
        sub = (to - _from) / 100

        for i in range(100):
            if self.animationRunning != this_animation:
                return

            self.window.setWindowOpacity(_from + i * sub)
            t = time.time()
            QApplication.processEvents()
            used = time.time() - t
            if used < 0.01:
                time.sleep(0.01 - used)
        self.window.setWindowOpacity(to)

        if self.animationRunning == this_animation:
            self.animationRunning = None

    @override
    def getMenuWidget(self):
        return self.menu

    @override
    def setupUi(self):
        self.menu = QMenu(self.menubar)
        self.menu.setTitle("Opacity")

        def _animation(opacity):
            return lambda: self._gradient(opacity)

        for alpha in range(100, 79, -5):
            self.menu.addAction(str(alpha) + "%", _animation(alpha / 100))

        for alpha in range(70, 29, -10):
            self.menu.addAction(str(alpha) + "%", _animation(alpha / 100))

    @staticmethod
    @override
    def priority():
        return -1
