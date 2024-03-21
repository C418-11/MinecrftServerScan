# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.2Dev"


from abc import ABC
from typing import Any


class ABCEvent(ABC):
    def __repr__(self):
        attr_str = ''
        for attr in self.__dict__:
            if attr.startswith('_'):
                continue
            attr_str += f"{attr}={repr(self.__dict__[attr])}, "

        attr_str = attr_str.rstrip(", ")
        return f"<{type(self).__name__} ({attr_str})>"

    def __str__(self):
        return repr(self)


class StartEvent(ABCEvent):
    def __init__(self, host: str, port: set[int]):
        self.host = host
        self.port = port


class FinishEvent(ABCEvent):
    def __init__(self, host: str, all_ports: set[int], finished_ports: set[int], error_ports:set[int]):
        self.host = host
        self.all_ports = all_ports
        self.finished_ports = finished_ports
        self.error_ports = error_ports


class ThreadErrorEvent(ABCEvent):
    def __init__(self, thread_id: str, error: BaseException, host: str, port: int):
        self.thread_id = thread_id
        self.error = error
        self.host = host
        self.port = port


class ThreadStartEvent(ABCEvent):
    def __init__(self, thread_id: str, host: str, port: int):
        self.thread_id = thread_id
        self.host = host
        self.port = port


class ThreadFinishEvent(ABCEvent):
    def __init__(self, thread_id: str, host: str, port: int, result: Any):
        self.thread_id = thread_id
        self.host = host
        self.port = port
        self.result = result
