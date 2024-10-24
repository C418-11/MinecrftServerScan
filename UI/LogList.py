# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import threading
from enum import StrEnum
from typing import override

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QListWidget

from UI.tools import showException


class LogLevel(StrEnum):
    NEVER = "Never"
    ALWAYS = "Always"

    DEBUG = "Debug"
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    CRITICAL = "Critical"


NonUsable = {LogLevel.NEVER, LogLevel.ALWAYS}


class LogListWidget(QListWidget):
    update_log_signal = pyqtSignal(name="update_log")

    def __init__(self, parent=None, log_batch_processing_delay: float = 0.5):
        super().__init__(parent)
        self._enable_log_levels: set[LogLevel] = {LogLevel(x) for x in LogLevel} - {LogLevel.NEVER}

        self._log_cache: list[tuple[list[str], str, LogLevel]] = []
        self._log_cache_lock = threading.Lock()

        self._log_timer: threading.Timer | None = None

        self.log_batch_processing_delay = log_batch_processing_delay

        self.enable_auto_scroll: bool = False

        # noinspection PyUnresolvedReferences
        self.update_log_signal.connect(self._update_log)
        # noinspection PyUnresolvedReferences
        self.verticalScrollBar().rangeChanged.connect(self._on_range_changed)

    def enableLogLevels(self, *args: LogLevel):
        self._enable_log_levels.update(args)

    def disableLogLevels(self, *args: LogLevel):
        """
        Disable log levels.
        Can be safely called multiple times.
        """
        self._enable_log_levels.difference_update(args)

    @override
    def setAutoScroll(self, enable: bool):
        """
        非原生实现 推荐直接更改属性enable_auto_scroll
        """
        self.enable_auto_scroll = enable

    @property
    def enable_log_levels(self) -> set[LogLevel]:
        return self._enable_log_levels.copy()

    @showException
    def _on_range_changed(self, *_):
        if self.enable_auto_scroll:
            self.scrollToBottom()

    @showException
    def _update_log(self):
        with self._log_cache_lock:
            for path, msg, level in self._log_cache:  # todo #b31b92875eca79ad3f9a451a853bf25d 后续考虑切换日志等级后刷新已经显示过的内容
                path_str = ''.join([f"[{r}]" for r in path])
                if level in NonUsable:
                    level = ''
                else:
                    level = f"{level}"

                if path_str and level:
                    path_str += ' '

                try:
                    self.addItem(f"{path_str}{level}: {msg}")
                except RuntimeError:
                    pass

            self._log_cache.clear()

    def updateLogNow(self):  # todo #b31b92875eca79ad3f9a451a853bf25d
        # noinspection PyUnresolvedReferences
        self.update_log_signal.emit()

    @override
    def clear(self):
        with self._log_cache_lock:
            super().clear()
            self._log_cache.clear()
            if self._log_timer is not None:
                self._log_timer.cancel()
                self._log_timer = None

    def log(self, root: list[str], txt: str, level: LogLevel):
        if level not in self._enable_log_levels:  # todo #b31b92875eca79ad3f9a451a853bf25d
            return

        with self._log_cache_lock:
            self._log_cache.append((root, txt, level))

        if self._log_timer is not None and self._log_timer.is_alive():
            return

        def _emit():
            try:
                # noinspection PyUnresolvedReferences
                self.update_log_signal.emit()
            except RuntimeError:
                pass

        self._log_timer = threading.Timer(self.log_batch_processing_delay, _emit)
        self._log_timer.daemon = True
        self._log_timer.start()

    def logAlways(self, root: list[str], txt: str):
        self.log(root, txt, LogLevel.ALWAYS)

    def logNever(self, root: list[str], txt: str):
        self.log(root, txt, LogLevel.NEVER)

    def logDebug(self, root: list[str], txt: str):
        self.log(root, txt, LogLevel.DEBUG)

    def logInfo(self, root: list[str], txt: str):
        self.log(root, txt, LogLevel.INFO)

    def logWarning(self, root: list[str], txt: str):
        self.log(root, txt, LogLevel.WARNING)

    def logError(self, root: list[str], txt: str):
        self.log(root, txt, LogLevel.ERROR)

    def logCritical(self, root: list[str], txt: str):
        self.log(root, txt, LogLevel.CRITICAL)


__all__ = ("LogLevel", "LogListWidget", "NonUsable",)
