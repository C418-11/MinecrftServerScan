# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

from abc import ABCMeta
from typing import Any, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAbstractSpinBox as ABCSpinBox
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QWidget

from .tools import showException


class SpinSupportRangeMeta(ABCMeta):
    __check_attrs = ("value", "setMaximum", "setMinimum", "valueChanged")

    @classmethod
    def __instancecheck__(cls, instance):
        for attr in cls.__check_attrs:
            if not hasattr(instance, attr):
                return NotImplemented
        return True

    @classmethod
    def __subclasscheck__(cls, subclass):
        for attr in cls.__check_attrs:
            if not hasattr(subclass, attr):
                return NotImplemented
        return True


class SpinSupportRange(metaclass=SpinSupportRangeMeta):
    ...


class RangedSpinBox(QWidget):
    """ A spin box with range """
    valueChanged = pyqtSignal(int, int)

    @showException
    def __init__(
            self,
            parent=None,
            maximum=None,
            minimum=None,
            spinbox_cls: tuple[type[ABCSpinBox], type[ABCSpinBox]] = (QSpinBox, QSpinBox),
    ):
        super().__init__(parent)
        if not all(issubclass(cls, SpinSupportRange) for cls in spinbox_cls):
            raise TypeError(f"spinbox_cls must be subclass of {SpinSupportRange.__name__}")

        self._min_box = spinbox_cls[0](self)
        self._max_box = spinbox_cls[1](self)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self._min_box)
        self.layout().addWidget(self._max_box)

        self._min_box.valueChanged.connect(self._on_min_changed)
        self._max_box.valueChanged.connect(self._on_max_changed)

        self._minimum_difference: Optional[Any] = None

        if minimum is not None:
            self._min_box.setMinimum(minimum)
        if maximum is not None:
            self._max_box.setMaximum(maximum)

    def _on_min_changed(self, value):
        if value > self._max_box.value():
            self._max_box.setValue(value)
        # noinspection PyUnresolvedReferences
        self.valueChanged.emit(*self.value())

    def _on_max_changed(self, value):
        if value < self._min_box.value():
            self._min_box.setValue(value)
        # noinspection PyUnresolvedReferences
        self.valueChanged.emit(*self.value())

    def value(self) -> tuple[Any, Any]:
        return self._min_box.value(), self._max_box.value()

    def setValue(self, minimum: Optional[Any] = None, maximum: Optional[Any] = None) -> None:
        if minimum is not None:
            self._min_box.setValue(minimum)
        if maximum is not None:
            self._max_box.setValue(maximum)

    def minimum(self) -> Any:
        return self._min_box.minimum()

    def setMinimum(self, value: Any) -> None:
        self._min_box.setMinimum(value)
        self._max_box.setMinimum(value)

    def maximum(self) -> Any:
        return self._max_box.maximum()

    def setMaximum(self, value: Any) -> None:
        self._min_box.setMaximum(value)
        self._max_box.setMaximum(value)

    def setRange(self, min_val: Optional[Any] = None, max_val: Optional[Any] = None) -> None:
        if min_val is not None:
            self.setMinimum(min_val)
        if max_val is not None:
            self.setMaximum(max_val)

    def setSingleStep(self, value: Any) -> None:
        self._min_box.setSingleStep(value)
        self._max_box.setSingleStep(value)

    def minimumSpinBox(self) -> ABCSpinBox:
        return self._min_box

    def maximumSpinBox(self) -> ABCSpinBox:
        return self._max_box

    def setAlignment(self, alignment: Qt.Alignment) -> None:
        self._min_box.setAlignment(alignment)
        self._max_box.setAlignment(alignment)

    def minimumDifference(self) -> Optional[Any]:
        return self._minimum_difference

    def setMinimumDifference(self, value: Optional[Any]) -> None:
        self._minimum_difference = value


__all__ = (
    "SpinSupportRangeMeta",
    "SpinSupportRange",
    "RangedSpinBox",
)
