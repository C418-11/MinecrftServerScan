# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"
__description__ = "Window topping"

from typing import override

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QMenuBar
from PyQt5.QtWidgets import QWidget

from UI.ABC import AbcMenu
from UI.RegisterUI import register_menu
from UI.tools import showException


class WindowTop(AbcMenu):
    def __init__(self, _menubar: QMenuBar, _window: QWidget):
        super().__init__(_menubar, _window)
        self.menu: QMenu | None = None

    @override
    def getMenuWidget(self):
        return self.menu

    @showException
    def on(self):
        self.window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.window.show()

    @showException
    def off(self):
        self.window.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.window.show()

    @override
    def setupUi(self):
        self.menu = QMenu(self.menubar)
        self.menu.setTitle("WindowTop")

        self.menu.addAction("On", lambda *_: self.on())
        self.menu.addAction("Off", lambda *_: self.off())

    @staticmethod
    @override
    def priority():
        return float("-inf")


register_menu(WindowTop)
