# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.5Dev"

import socket
import struct
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Callable

from func_timeout import func_timeout

from .Events import ABCEvent
from .Events import FinishEvent
from .Events import StartEvent
from .Events import ThreadErrorEvent
from .Events import ThreadFinishEvent
from .Events import ThreadStartEvent


def _make_packet(data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + data


def analyze_varint(data) -> int:
    result = 0
    shift = 0
    for raw_byte in data:
        val_byte = raw_byte & 0x7F
        result |= val_byte << shift
        if raw_byte & 0x80 == 0:
            break
        shift += 7
    return result


def read_packet(client: socket.socket) -> bytes:
    """读取包"""
    # 读取数据包长度
    length = analyze_varint(client.recv(2))
    # 获取足够长的数据
    return _recv_all(length, client)


def _recv_all(length: int, client: socket.socket):
    data = b""
    while len(data) < length:
        more = client.recv(length - len(data))
        if not more:
            raise EOFError
        data += more
    return data


class Scanner:
    protocol_version = 65

    def __init__(
            self,
            host: str,
            port: set[int],
            /,
            callback: Callable[[ABCEvent], Any],
            *,
            max_threads: int | None = 1,
    ) -> None:

        """
        :param host: 目标ip | 目标域名
        :param port: 目标端口集合
        :param callback: 回调 用于处理扫描结果
        :param max_threads: 最大同时存在的线程数 为None时表示不限制
        """

        if max_threads is not None and max_threads < 1:
            raise ValueError("max_threads must be greater than 1")

        if max_threads is None:
            max_threads = len(port)

        self._host = host
        self._port = port
        self._callback = callback

        self.finished_ports: set[int] = set()
        self.error_ports: set[int] = set()
        self.update_ports_lock = threading.Lock()

        self._max_threads = max_threads

        self._wait_finish_thread: threading.Thread | None = None
        self._thread_pool: ThreadPoolExecutor | None = None

        self.start_timestamp_ns: int | None = None
        self.end_timestamp_ns: int | None = None

        self.connect_timeout = 0.1
        self.scan_timeout = 1

    def _wrapper(self, port: int, thread_id: str):
        def _runner() -> None:
            try:
                self._scan(port, thread_id)
            except Exception as err:
                self._callback(ThreadErrorEvent(thread_id=thread_id, host=self._host, port=port, error=err))
                with self.update_ports_lock:
                    self.error_ports.add(port)

        func_timeout(
            self.scan_timeout,
            _runner
        )

    def _scan(self, port, thread_id) -> None:
        self._callback(ThreadStartEvent(thread_id=thread_id, host=self._host, port=port))

        client = socket.create_connection((self._host, port), timeout=self.connect_timeout)

        client.sendall(self._make_handshake_packet(port))
        client.sendall(_make_packet(b'\x00'))
        raw_data = read_packet(client)

        self._callback(ThreadFinishEvent(thread_id=thread_id, host=self._host, port=port, result=raw_data))
        with self.update_ports_lock:
            self.finished_ports.add(port)

    def _wait_finish(self):
        try:
            self._thread_pool.shutdown(wait=True, cancel_futures=False)
            self.end_timestamp_ns = time.time_ns()

            self._callback(FinishEvent(
                host=self._host,
                all_ports=self._port,
                finished_ports=self.finished_ports,
                error_ports=self.error_ports,
                used_time_ns=self.end_timestamp_ns - self.start_timestamp_ns,
            ))
        except Exception as err:
            traceback.print_exception(err)
            time.sleep(10)

    def start(self) -> None:
        self.start_timestamp_ns = time.time_ns()
        self._callback(StartEvent(self._host, self._port))

        self._thread_pool = ThreadPoolExecutor(max_workers=self._max_threads)

        for port in self._port:
            thread_id = uuid.uuid4().hex
            self._thread_pool.submit(self._wrapper, *(port, thread_id))

        self._wait_finish_thread = threading.Thread(target=self._wait_finish, daemon=True)
        self._wait_finish_thread.start()

    def join(self) -> None:
        self._thread_pool.shutdown(wait=True)
        self._wait_finish_thread.join()

    def stop(self, wait: bool = True, cancel_futures: bool = True):
        self._thread_pool.shutdown(wait=wait, cancel_futures=cancel_futures)

    def is_alive(self) -> bool:
        return self._wait_finish_thread.is_alive()

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
