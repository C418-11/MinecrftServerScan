# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.4Dev"

import traceback
import warnings
from typing import override

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from GlobalConfigs import MinimumSize
from UI.ABC import AbcUI
from UI.tools import showException


class MoveProxyMenuBar(QMenuBar):
    def __init__(self, *args, move, **kwargs):
        super().__init__(*args, **kwargs)

        self._move_func = move

        self.base_position = None

    @showException
    @override
    def mousePressEvent(self, event, *_):
        # noinspection PyUnresolvedReferences
        if event.button() == Qt.LeftButton:
            self.base_position = event.screenPos(), event.localPos()
        super().mousePressEvent(event)

    @showException
    @override
    def mouseMoveEvent(self, event, *_):

        # noinspection PyUnresolvedReferences
        if event.buttons() == Qt.LeftButton:
            if abs(self.base_position[0].x() - event.screenPos().x()) > 0.8 and abs(
                    self.base_position[0].y() - event.screenPos().y()) > 0.8:

                f_pos = event.screenPos() - self.base_position[1]
                pos = QPoint(round(f_pos.x()), round(f_pos.y() - 6.5))
                if not self._move_func(pos):
                    event.accept()
                else:
                    event.ignore()
            else:
                self.base_position = event.screenPos(), event.localPos()
                event.accept()


class UiMain:
    def __init__(self, window: QMainWindow):
        self.Window: QMainWindow = window
        self.Widget: QWidget | None = None

        self.CtrlBar: QWidget | None = None
        self.MenuBar: MoveProxyMenuBar | None = None
        self.TopTab: QTabWidget | None = None

        self.MaxNormalButton: QPushButton | None = None
        self.MinButton: QPushButton | None = None
        self.ExitButton: QPushButton | None = None

        self.top_tabs: list[AbcUI] = []

    def append(self, subpage: type[AbcUI]):
        subpage = subpage(self.TopTab, self)
        subpage.setupUi()
        self.TopTab.addTab(subpage.getMainWidget(), subpage.getTagName())
        self.top_tabs.append(subpage)

    @showException
    def _MinSlot(self, *_, **__):
        if self.Window.isMaximized():
            self._MaxNormalSlot()
        self.Window.showMinimized()

    @showException
    def _MaxNormalSlot(self, *_, **__):
        if self.Window.isMaximized():
            self.Window.showNormal()
            try:
                self.Window.setGeometry(self.Window.NormalGeometry)
            except AttributeError:
                warnings.warn(
                    f"Window {self.Window} has no NormalGeometry",
                    RuntimeWarning,
                    stacklevel=0
                )
            self.MaxNormalButton.setText("Max")
        else:
            self.Window.NormalGeometry = self.Window.geometry()
            self.Window.showMaximized()
            self.MaxNormalButton.setText("Normal")

    @showException
    def _ExitSlot(self, *_, **__):
        self.Window.close()

        for tab in self.top_tabs:
            try:
                func = tab.exit
            except AttributeError:
                continue

            try:
                func()
            except Exception as e:
                traceback.print_exception(e)

    def setupUi(self):
        self.Widget = QWidget(self.Window)
        self.Widget.setObjectName("MainWindowWidget")
        self.Widget.resize(*MinimumSize)
        self.Widget.setMinimumSize(*MinimumSize)
        self.Window.setCentralWidget(self.Widget)

        self.TopTab = QTabWidget(self.Widget)
        self.TopTab.setObjectName("TopTab")

        self.CtrlBar = QWidget(self.Widget)
        self.CtrlBar.setObjectName("CtrlBar")

        self.MenuBar = MoveProxyMenuBar(self.CtrlBar, move=self.SafeMove)
        self.MenuBar.setObjectName("MenuBar")

        self.ExitButton = QPushButton(self.CtrlBar)
        self.ExitButton.setObjectName("ExitButton")

        self.MaxNormalButton = QPushButton(self.CtrlBar)
        self.MaxNormalButton.setObjectName("MaxNormalButton")

        self.MinButton = QPushButton(self.CtrlBar)
        self.MinButton.setObjectName("MinButton")

        self.Widget.setLayout(QVBoxLayout(self.Widget))
        self.Widget.layout().setContentsMargins(0, 0, 0, 0)
        self.Widget.layout().addWidget(self.CtrlBar)
        self.Widget.layout().addWidget(self.TopTab)
        self.CtrlBar.setLayout(QHBoxLayout(self.CtrlBar))
        self.CtrlBar.layout().setContentsMargins(0, 0, 0, 0)
        self.CtrlBar.layout().setSpacing(0)
        self.CtrlBar.layout().addWidget(self.MenuBar)
        self.CtrlBar.layout().addWidget(self.MinButton)
        self.CtrlBar.layout().addWidget(self.MaxNormalButton)
        self.CtrlBar.layout().addWidget(self.ExitButton)

        QWidget.setTabOrder(self.MenuBar, self.MinButton)
        QWidget.setTabOrder(self.MinButton, self.MaxNormalButton)
        QWidget.setTabOrder(self.MaxNormalButton, self.ExitButton)

        self.ReTranslateUi()

        # noinspection PyUnresolvedReferences
        self.ExitButton.clicked.connect(self._ExitSlot)
        # noinspection PyUnresolvedReferences
        self.MinButton.clicked.connect(self._MinSlot)
        # noinspection PyUnresolvedReferences
        self.MaxNormalButton.clicked.connect(self._MaxNormalSlot)

        self.TopTab.setCurrentIndex(0)

        # noinspection PyArgumentList
        QMetaObject.connectSlotsByName(self.Widget)

    @showException
    def SafeMove(self, *point):
        if self.Window.isMaximized():
            return True

        pos = QPoint(*point)

        x, y = pos.x(), pos.y()

        # 保持窗口在屏幕内
        screen_size = self.Window.screen().size()

        x = max(min(x, screen_size.width() - self.Window.width()), 0)
        y = max(min(y, screen_size.height() - self.CtrlBar.height()), 0)

        self.Window.move(x, y)

    def ReTranslateUi(self):
        self.Window.setWindowTitle(u"MC服务器扫描工具")
        self.ExitButton.setText(u"Exit")
        self.MinButton.setText(u"Min")

        if self.Widget.isMaximized():
            self.MaxNormalButton.setText(u"Normal")
        else:
            self.MaxNormalButton.setText(u"Max")


__all__ = ("UiMain",)
