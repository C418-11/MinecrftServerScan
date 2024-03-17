# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import json
import os
import socket
import threading
from typing import override

from PyQt5.QtCore import Qt, QModelIndex, QSize
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal

from Lib.MinecraftColorString import ColorString
from Lib.ParseMCServerInfo import ServerInfo
from MinecraftServerScanner.Events import ThreadFinishEvent, ThreadErrorEvent, FinishEvent, StartEvent, \
    ThreadStartEvent, ABCEvent
from MinecraftServerScanner.Scanner import Scanner
from UI.ABC import AbcUI
from UI.tools import showException
from Lib.Configs import read_default_yaml, BASE_PATH, FontFamily, NormalFont
from UI.RegisterUI import register

from PyQt5.QtWidgets import QLineEdit, QProgressBar, QHBoxLayout

from enum import IntEnum

# noinspection SpellCheckingInspection
_load_scan_server = read_default_yaml(
    os.path.join(BASE_PATH, 'ScanServer.yaml'),
    {
        "DefaultTarget": [
            "127.0.0.1",
            "s2.wemc.cc",
            "cl-sde-bgp-1.openfrp.top",
            "cn-bj-bgp-2.openfrp.top",
            "cn-bj-bgp-4.openfrp.top",
            "cn-bj-plc-1.openfrp.top",
            "cn-bj-plc-2.openfrp.top",
            "cn-cq-plc-1.openfrp.top",
            "cn-fz-plc-1.openfrp.top",
            "cn-he-plc-1.openfrp.top",
            "cn-he-plc-2.openfrp.top",
            "cn-hk-bgp-4.openfrp.top",
            "cn-hk-bgp-5.openfrp.top",
            "cn-hk-bgp-6.openfrp.top",
            "cn-hz-bgp-1.openfrp.top",
            "cn-nd-plc-1.openfrp.top",
            "cn-qz-plc-1.openfrp.top",
            "cn-sc-plc-2.openfrp.top",
            "cn-sy-dx-2.openfrp.top",
            "cn-sz-bgp-1.openfrp.top",
            "cn-sz-plc-1.openfrp.top",
            "cn-wh-plc-1.openfrp.top",
            "cn-yw-plc-1.openfrp.top",
            "jp-osk-bgp-1.openfrp.top",
            "kr-nc-bgp-1.openfrp.top",
            "kr-se-cncn-1.openfrp.top",
            "ru-mow-bgp-1.openfrp.top",
            "us-sjc-bgp-1.openfrp.top",
            "us-sjc-bgp-2.openfrp.top"
        ]
    })


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


def _read_packet(client: socket.socket) -> bytes:
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


class LogLevel(IntEnum):
    NEVER = -1
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


class CallbackPushButton(QPushButton):
    callback_signal = pyqtSignal(ABCEvent, name="callback")
    log_signal = pyqtSignal(name="log")

    def __init__(self, *args):
        super().__init__(*args)


def _spawn_info_widget(server_info: ServerInfo, host: str, port: int):
    widget = QWidget()
    root_layout = QHBoxLayout()
    root_layout.setContentsMargins(0, 0, 0, 0)
    widget.setLayout(root_layout)

    pixmap = QPixmap("./DefaultServerIcon.png")

    if server_info.favicon is not None:
        image_bytes = server_info.favicon.to_bytes()
        pixmap.loadFromData(image_bytes)

    image_label = QLabel()
    pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    image_label.setPixmap(pixmap)
    image_label.setFixedSize(QSize(64, 64))

    desc_layout = QVBoxLayout()
    desc_layout.setContentsMargins(0, 0, 0, 0)

    host_ip_label = QLabel()
    host_ip_label.setText(f"{host}:{port}")
    host_ip_label.setAlignment(Qt.AlignCenter)
    font_height = host_ip_label.fontMetrics().height()
    host_ip_label.setFixedHeight(font_height)

    desc_label = QLabel()

    desc_html = ColorString.from_string(server_info.description.to_string()).to_html()
    desc_html = desc_html.replace(
        "<span style='color: rgb(255, 255, 255);'>",
        "<span style='color: rgb(255, 255, 255); background-color: rgb(220, 220, 220);'>"
    )
    desc_html = f"<span>{desc_html.replace('\n', "<br/>")}</span>"
    desc_label.setText(desc_html)

    root_layout.addWidget(image_label)
    root_layout.addLayout(desc_layout)
    desc_layout.addWidget(host_ip_label)
    desc_layout.addWidget(desc_label)

    return widget


class ServerScan(AbcUI):
    def __init__(self, _parent: QTabWidget):
        super().__init__(_parent)

        self.widget: QScrollArea | None = None

        self.ip_input: QComboBox | None = None

        self.scan_button: CallbackPushButton | None = None
        self.show_log: QListWidget | None = None

        self.result_count_label: QLabel | None = None
        self.show_result_list: QListWidget | None = None
        self.progress_bar: QProgressBar | None = None

        self.scanner: Scanner | None = None
        self.ports = {x for x in range(1000, 65536)}

        self.result_ls: list[ServerInfo] = []

        self.log_ls = []
        self.log_cache = []
        self.last_log: threading.Timer | None = None
        self.log_cache_lock = threading.Lock()

        self.log_level = LogLevel.INFO

    @showException
    def _callback(self, event):
        def _parse_thread_finish(e: ThreadFinishEvent):
            try:
                parsed = json.loads(e.result[3:].decode())
            except Exception as err:
                self._log([e.port], f"解析失败 Error: {type(err).__name__}: {err}", LogLevel.ERROR)
                return

            self._log([e.port], f"存在服务器", LogLevel.INFO)

            server_info = ServerInfo(parsed)
            self.result_ls.append(server_info)
            self.result_count_label.setText(f"扫描结果: {len(self.result_ls)}")

            item = QListWidgetItem()
            item.setData(Qt.UserRole, (server_info, e.host, e.port))

            widget = _spawn_info_widget(server_info, e.host, e.port)

            item.setSizeHint(QSize(0, 64))

            self.show_result_list.addItem(item)
            self.show_result_list.setItemWidget(item, widget)

        def _parse_thread_error(e: ThreadErrorEvent):
            if type(e.error) is TimeoutError:
                return
            if type(e.error) is socket.gaierror:
                return
            self._log([e.port], f"意外的错误 {type(e.error).__name__}: {e.error}", LogLevel.ERROR)

        def _parse_start(e: StartEvent):
            self._log([e.host], f"开始扫描 共计{len(e.port)}个端口")
            self.scan_button.setEnabled(False)
            self.ip_input.setEnabled(False)

            self.log_ls.clear()
            self.result_ls.clear()

            self.show_result_list.clear()

            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(len(self.ports))
            self.progress_bar.setValue(0)
            self.progress_bar.setToolTip("正在扫描...")

            self.result_count_label.setText("正在扫描...")

        def _parse_finish(e: FinishEvent):
            self._log([], f"扫描完成", LogLevel.INFO)
            self.result_count_label.setText(f"扫描结果: {len(self.result_ls)}")
            self.progress_bar.setToolTip(f"扫描结束 共计扫描{len(e.port)}个端口")
            self.scan_button.setEnabled(True)
            self.ip_input.setEnabled(True)
            self.scan_button.setToolTip('点击开始')
            self.ip_input.setToolTip('')

        if type(event) is ThreadStartEvent:
            return

        if type(event) is ThreadFinishEvent:
            _parse_thread_finish(event)
        elif type(event) is ThreadErrorEvent:
            _parse_thread_error(event)
        elif type(event) is StartEvent:
            _parse_start(event)
            return
        elif type(event) is FinishEvent:
            _parse_finish(event)
            return

        self.progress_bar.setValue(self.progress_bar.value() + 1)
        self.progress_bar.setToolTip(f"正在扫描{self.progress_bar.value()}/{self.progress_bar.maximum()}")

    @showException
    def _start_scan(self, *_):
        self._log([], f"准备扫描")
        self.scan_button.setEnabled(False)
        self.scan_button.setToolTip("正在扫描请勿重复操作...")
        self.ip_input.setEnabled(False)
        self.ip_input.setToolTip("正在扫描请勿重复操作...")

        def _emit(e: ABCEvent):
            # noinspection PyUnresolvedReferences
            self.scan_button.callback_signal.emit(e)

        self.scanner = Scanner(
            self.ip_input.currentText(),
            self.ports,
            _emit,
            socket_reader=_read_packet,
            max_threads=256,
        )
        self.scanner.connect_timeout = 0.9
        self.scanner.scan_timeout = 2

        self.scanner.start()

    @showException
    def _log(self, root: list, txt: str, level=LogLevel.INFO):
        if level < self.log_level:
            return

        with self.log_cache_lock:
            self.log_cache.append((root, txt))

        if self.last_log is not None and self.last_log.is_alive():
            return

        def _emit():
            try:
                # noinspection PyUnresolvedReferences
                self.scan_button.log_signal.emit()
            except RuntimeError:
                pass

        self.last_log = threading.Timer(0.5, _emit)
        self.last_log.daemon = True
        self.last_log.start()

    @showException
    def _update_log(self):
        for _path, _msg in self.log_cache:
            self.log_ls.append((_path, _msg))

            path_str = ''.join([f"[{r}]" for r in _path])
            try:
                self.show_log.addItem(f"{path_str}: {_msg}")
            except RuntimeError:
                pass

        self.log_cache.clear()

    @showException
    def _showServerDetails(self, item: QListWidgetItem):
        index = self.show_result_list.indexFromItem(item)
        index: QModelIndex
        server_info = self.result_ls[index.row()]

        _, host, port = item.data(Qt.UserRole)

        html_space = "&nbsp;"

        if server_info.players.sample is not None:
            player_list_str = "玩家列表:\n"
            player_list_str += '\n'.join(
                [
                    f"{html_space * 4}{player.name.to_html()}{html_space}({player.id})"
                    for player in server_info.players.sample
                ]
            )
            player_list_str += '\n'
        else:
            player_list_str = ''

        description = ColorString.from_string(server_info.description.to_string()).to_html()
        description_list = description.split('\n')
        description_html = '\n'.join(
            [f"{html_space * 4}{line}" for line in description_list]
        )

        message = "<span>"
        message += f"服务端版本: {server_info.version.name}\n"
        message += f"服务器描述:\n{description_html}\n"
        message += f"在线玩家: {server_info.players.online}/{server_info.players.max}\n"
        message += player_list_str
        message += f"服务器地址: {host, port}"
        message += "</span>"
        message = message.replace("\n", "<br/>")

        message = message.replace(
            "<span style='color: rgb(255, 255, 255);'>",
            "<span style='color: rgb(255, 255, 255); background-color: rgb(220, 220, 220);'>"
        )

        msg_box = QMessageBox()
        msg_box.setWindowTitle("服务器详情")
        msg_box.setText(message)

        msg_box.exec()

    @override
    def setupUi(self):
        self.widget = QScrollArea(self._parent)
        self.widget.setFont(QFont(FontFamily, NormalFont))

        self.ip_input = QComboBox(self.widget)
        self.ip_input.setEditable(True)
        QLineEdit.setPlaceholderText(self.ip_input.lineEdit(), "IP地址或域名...")
        QLineEdit.setAlignment(self.ip_input.lineEdit(), Qt.AlignCenter)

        self.ip_input.addItems(_load_scan_server["DefaultTarget"])

        self.scan_button = CallbackPushButton("扫描", self.widget)
        self.scan_button.setToolTip("点击开始")
        # noinspection PyUnresolvedReferences
        self.scan_button.clicked.connect(self._start_scan)
        # noinspection PyUnresolvedReferences
        self.scan_button.callback_signal.connect(self._callback)
        # noinspection PyUnresolvedReferences
        self.scan_button.log_signal.connect(self._update_log)

        self.result_count_label = QLabel("未进行过扫描", self.widget)
        self.result_count_label.setAlignment(Qt.AlignCenter)

        self.show_log = QListWidget(self.widget)
        self.show_log.setToolTip("扫描日志")
        self.show_log.addItem('Made By: C418____11\n')
        self.show_log.setStyleSheet("background-color: rgba(255, 0, 0, 64);")

        self.show_result_list = QListWidget(self.widget)
        self.show_result_list.setToolTip("扫描结果")
        # noinspection PyUnresolvedReferences
        self.show_result_list.itemDoubleClicked.connect(self._showServerDetails)

        self.progress_bar = QProgressBar(self.widget)
        self.progress_bar.setToolTip("未开始扫描")
        self.progress_bar.setMinimum(0)

    @override
    @showException
    def ReScale(self, x_scale: float, y_scale: float):
        font_height = self.ip_input.fontMetrics().height()

        self.scan_button.resize(
            int(self.widget.width() * 0.199),
            int(font_height * 1.5 * y_scale)
        )

        self.ip_input.resize(
            int(self.widget.width() * 0.799),
            int(font_height * 1.5 * y_scale)
        )

        self.ip_input.move(
            int((self.widget.width() - self.ip_input.width() - self.scan_button.width()) / 2),
            0
        )

        self.scan_button.move(
            self.ip_input.x() + self.ip_input.width(),
            self.ip_input.y()
        )

        self.result_count_label.setFixedWidth(self.widget.width())

        self.result_count_label.move(
            int((self.widget.width() - self.result_count_label.width()) / 2),
            self.ip_input.height()
        )

        self.show_result_list.resize(self.widget.width(), int(0.5 * self.widget.height()))
        self.show_result_list.move(0, self.result_count_label.y() + self.result_count_label.height())

        self.progress_bar.resize(self.widget.width(), int(30 * y_scale))
        self.progress_bar.move(0, self.widget.height() - self.progress_bar.height())

        self.show_log.resize(self.widget.width(), int(0.3 * self.widget.height()))
        self.show_log.move(0, self.progress_bar.y() - self.show_log.height())

    @override
    def getMainWidget(self):
        return self.widget

    @override
    def getTagName(self):
        return "服务器扫描"


register(ServerScan)
