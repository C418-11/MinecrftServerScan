# -*- coding: utf-8 -*-
# cython: language_level = 3


from abc import ABC
from abc import abstractmethod

from PyQt5.QtWidgets import *


class AbcUI(ABC):
    def __init__(self, _parent: QTabWidget):
        self._parent = _parent

    def ReScale(self, x_scale: float, y_scale: float):
        ...

    def exit(self):
        ...

    @abstractmethod
    def setupUi(self):
        ...

    @abstractmethod
    def getMainWidget(self):
        ...

    @abstractmethod
    def getTagName(self):
        ...

    @staticmethod
    def priority():
        return 0


class AbcMenu(ABC):
    def __init__(self, _menubar: QMenuBar, _window: QWidget):
        self.menubar = _menubar
        self.window = _window

    @abstractmethod
    def setupUi(self):
        ...

    @abstractmethod
    def getMenuWidget(self):
        ...

    @staticmethod
    def priority():
        return 0
