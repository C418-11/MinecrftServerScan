# -*- coding: utf-8 -*-
# cython: language_level = 3


from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Optional

from PyQt5.QtWidgets import *


class AbcUI(ABC):
    def __init__(self, _parent: QTabWidget, _main_ui: Optional[Any]):
        self._parent = _parent
        if _main_ui is not None:
            self._main_ui = _main_ui

    def exit(self):
        ...

    @abstractmethod
    def reTranslate(self):
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
    def __init__(self, _menubar: QMenuBar, _window: QMainWindow):
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
