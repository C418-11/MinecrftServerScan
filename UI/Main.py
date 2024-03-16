# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.3Dev"

import traceback
import warnings
from typing import override

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from Lib.Configs import MinimumSize
from UI.ABC import AbcUI
from UI.BaseWidgets import GetScale
from UI.tools import showException


class CustomQMenuBar(QMenuBar):
    def __init__(self, *args, move, **kwargs):
        super().__init__(*args, **kwargs)

        self._move_func = move

        self.base_position = None

    @showException
    @override
    def mousePressEvent(self, event, *_):
        # noinspection PyUnresolvedReferences
        root_is_maximized = self.parent().parent().isMaximized()

        # noinspection PyUnresolvedReferences
        if event.button() == Qt.LeftButton and not root_is_maximized:
            self.base_position = event.screenPos(), event.localPos()
        super().mousePressEvent(event)

    @showException
    @override
    def mouseMoveEvent(self, event, *_):
        # noinspection PyUnresolvedReferences
        root_is_maximized = self.parent().parent().isMaximized()

        # noinspection PyUnresolvedReferences
        if event.buttons() == Qt.LeftButton and not root_is_maximized:
            if abs(self.base_position[0].x() - event.screenPos().x()) > 0.8 and abs(
                    self.base_position[0].y() - event.screenPos().y()) > 0.8:

                f_pos = event.screenPos() - self.base_position[1]
                pos = QPoint(round(f_pos.x()), round(f_pos.y() - 6.5))
                self._move_func(pos)
            else:
                self.base_position = event.screenPos(), event.localPos()

            event.accept()


class UiMain:
    def __init__(self, widget: GetScale):
        super().__init__()
        self.Widget = widget
        self.Widget.reference_size = QSize(*MinimumSize)
        self.Widget.resize(*MinimumSize)
        self.Widget.setMinimumSize(*MinimumSize)

        self.TopTab: QTabWidget | None = None
        self.TopTab_Widget: QWidget | None = None

        self.CtrlBar: QWidget | None = None
        self.MenuBar: CustomQMenuBar | None = None

        self.MaxNormalButton: QPushButton | None = None
        self.MinButton: QPushButton | None = None
        self.ExitButton: QPushButton | None = None

        self.top_tabs: list[AbcUI] = []

    def append(self, subpage: type[AbcUI]):
        subpage = subpage(self.TopTab)
        subpage.setupUi()
        self.TopTab.addTab(subpage.getMainWidget(), subpage.getTagName())
        self.top_tabs.append(subpage)

    @showException
    def _MinSlot(self, *_, **__):
        if self.Widget.isMaximized():
            self._MaxNormalSlot()
        self.Widget.showMinimized()

    @showException
    def _MaxNormalSlot(self, *_, **__):
        if self.Widget.isMaximized():
            self.Widget.showNormal()
            try:
                self.Widget.setGeometry(self.Widget.NormalGeometry)
            except AttributeError:
                warnings.warn(
                    f"Widget {self.Widget} has no NormalGeometry",
                    RuntimeWarning,
                    stacklevel=0
                )
            self.MaxNormalButton.setText(u"Max")
        else:
            self.Widget.NormalGeometry = self.Widget.geometry()
            self.Widget.showMaximized()
            self.MaxNormalButton.setText(u"Normal")

    @showException
    def _ExitSlot(self, *_, **__):
        self.Widget.close()

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
        self.TopTab = QTabWidget(self.Widget)
        self.TopTab.setObjectName(u"TopTab")

        self.TopTab_Widget = QWidget()
        self.TopTab_Widget.setObjectName(u"TopTab_Widget")

        self.CtrlBar = QWidget(self.Widget)
        self.CtrlBar.setObjectName(u"CtrlBar")

        self.MenuBar = CustomQMenuBar(self.CtrlBar, move=self.SafeMove)
        self.MenuBar.setObjectName(u"Menu")

        self.ExitButton = QPushButton(self.CtrlBar)
        self.ExitButton.setObjectName(u"ExitButton")

        self.MaxNormalButton = QPushButton(self.CtrlBar)
        self.MaxNormalButton.setObjectName(u"MaxNormalButton")

        self.MinButton = QPushButton(self.CtrlBar)
        self.MinButton.setObjectName(u"MinButton")

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

        self.Widget.scaleChanged.connect(self.AutoResize)

        # noinspection PyArgumentList
        QMetaObject.connectSlotsByName(self.Widget)

        # noinspection PyUnresolvedReferences
        self.TopTab.currentChanged.connect(lambda *_: self.AutoResize(self.Widget.scaleWidth, self.Widget.scaleHeight))

    @showException
    def SafeMove(self, *point):

        pos = QPoint(*point)

        x, y = pos.x(), pos.y()

        # 保持窗口在屏幕内
        screen_size = self.Widget.screen().size()

        x = max(min(x, screen_size.width() - self.Widget.width()), 0)
        y = max(min(y, screen_size.height() - self.CtrlBar.height()), 0)

        self.Widget.move(x, y)

    @showException
    def AutoResize(self, x_scale: float, y_scale: float):
        self.CtrlBar.resize(self.Widget.width(), int(25 * y_scale))

        self.ExitButton.resize(int(60 * x_scale), self.CtrlBar.height())
        self.MinButton.resize(int(60 * x_scale), self.CtrlBar.height())
        self.MaxNormalButton.resize(int(60 * x_scale), self.CtrlBar.height())

        self.ExitButton.move(self.Widget.width() - self.ExitButton.width(), 0)
        self.MaxNormalButton.move(self.ExitButton.x() - self.MaxNormalButton.width(), 0)
        self.MinButton.move(self.MaxNormalButton.x() - self.MinButton.width(), 0)

        self.MenuBar.resize(self.MinButton.x(), self.CtrlBar.height())

        self.TopTab.resize(self.Widget.width(), self.Widget.height() - self.CtrlBar.height())
        self.TopTab.move(0, self.CtrlBar.height())

        try:
            feature_obj = self.top_tabs[self.TopTab.currentIndex()]
        except IndexError:
            return

        try:
            func = feature_obj.ReScale
        except AttributeError:
            return
        try:
            func(x_scale, y_scale)
        except Exception as e:
            traceback.print_exception(e)

    def ReTranslateUi(self):
        self.Widget.setWindowTitle(u"StatusRecorder")
        self.ExitButton.setText(u"Exit")
        self.MinButton.setText(u"Min")

        if self.Widget.isMaximized():
            self.MaxNormalButton.setText(u"Normal")
        else:
            self.MaxNormalButton.setText(u"Max")


__all__ = ("UiMain",)
