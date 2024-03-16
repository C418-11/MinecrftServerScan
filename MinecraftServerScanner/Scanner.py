# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.2Dev"

import struct
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Callable
from typing import Any
from func_timeout import func_timeout

import socket
from .Events import ABCEvent
from .Events import StartEvent
from .Events import FinishEvent
from .Events import ThreadStartEvent
from .Events import ThreadFinishEvent
from .Events import ThreadErrorEvent


def _make_packet(data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + data


def _analyze_varint(data) -> int:
    result = 0
    shift = 0
    for raw_byte in data:
        val_byte = raw_byte & 0x7F
        result |= val_byte << shift
        if raw_byte & 0x80 == 0:
            break
        shift += 7
    return result


class Scanner:
    protocol_version = 65

    def __init__(
            self,
            host: str,
            port: set[int],
            /,
            callback: Callable[[ABCEvent], Any],
            *,
            socket_reader: Callable[[socket.socket], bytes],
            max_threads: int | None = 1,
    ) -> None:

        """
        :param host: 目标ip | 目标域名
        :param port: 目标端口集合
        :param callback: 回调 用于处理扫描结果
        :param max_threads: 最大同时存在的线程数 为None时表示不限制
        :param socket_reader: 读取数据包并返回读取到的数据
        """

        if max_threads is not None and max_threads < 1:
            raise ValueError("max_threads must be greater than 1")

        if max_threads is None:
            max_threads = len(port)

        self._host = host
        self._port = port
        self._callback = callback

        self._socket_reader = socket_reader

        self._max_threads = max_threads

        self._thread_pool: ThreadPoolExecutor | None = None

        self.connect_timeout = 0.1
        self.scan_timeout = 1

    def _wrapper(self, port: int, thread_id: str):
        def _runner() -> None:
            try:
                self._scan(port, thread_id)
            except Exception as err:
                self._callback(ThreadErrorEvent(thread_id=thread_id, host=self._host, port=port, error=err))

        func_timeout(
            self.scan_timeout,
            _runner
        )

    def _scan(self, port, thread_id) -> None:
        self._callback(ThreadStartEvent(thread_id=thread_id, host=self._host, port=port))

        client = socket.create_connection((self._host, port), timeout=self.connect_timeout)

        client.sendall(self._make_handshake_packet(port))
        client.sendall(_make_packet(b'\x00'))
        raw_data = self._socket_reader(client)

        self._callback(ThreadFinishEvent(thread_id=thread_id, host=self._host, port=port, result=raw_data))

    def _wait_finish(self):
        self._thread_pool.shutdown(wait=True, cancel_futures=False)

        self._callback(FinishEvent(host=self._host, port=self._port))

    def start(self) -> None:
        self._callback(StartEvent(self._host, self._port))

        self._thread_pool = ThreadPoolExecutor(max_workers=self._max_threads)

        for port in self._port:
            thread_id = uuid.uuid4().hex
            self._thread_pool.submit(self._wrapper, *(port, thread_id))

        threading.Thread(target=self._wait_finish, daemon=True).start()

    def join(self) -> None:
        self._thread_pool.shutdown(wait=True)

    def stop(self, wait: bool = True, cancel_futures: bool = True):
        self._thread_pool.shutdown(wait=wait, cancel_futures=cancel_futures)

    def _make_handshake_packet(self, port: int) -> bytes:
        data = (
                b"\x00"
                + self.protocol_version.to_bytes(1, "little", signed=True)
                + struct.pack(">b", len(self._host))
                + self._host.encode("utf-8")
                + struct.pack(">h", port - 32768)
                + b"\x01"
        )
        return _make_packet(data)


__all__ = ("Scanner",)
