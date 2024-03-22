# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import json
import os
import socket
import threading
from typing import override, Callable

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
from UI.LogList import LogLevel, LogListWidget, NonUsable

from PyQt5.QtWidgets import QLineEdit, QProgressBar, QHBoxLayout, QApplication, QSpinBox

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


class CallbackPushButton(QPushButton):
    callback_signal = pyqtSignal(ABCEvent, name="callback")

    def __init__(self, *args):
        super().__init__(*args)


def _html_add_background_color(
        target_color: tuple[int, int, int],
        background_color: tuple[int, int, int],
        html_text: str
) -> str:
    text_rgb_str = f"rgb({target_color[0]}, {target_color[1]}, {target_color[2]})"
    background_rgb_str = f"rgb({background_color[0]}, {background_color[1]}, {background_color[2]})"

    return html_text.replace(
        f"<span style='color: {text_rgb_str};'>",
        f"<span style='color: {text_rgb_str}; background-color: {background_rgb_str};'>"
    )


def _spawn_info_widget(server_info: ServerInfo, host: str, port: int, *, is_window_top: Callable[[], bool]):
    widget = QWidget()
    widget.setToolTip("双击显示详细信息")
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
    root_layout.addWidget(image_label)

    desc_layout = QVBoxLayout()
    desc_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.addLayout(desc_layout)

    state_layout = QHBoxLayout()
    state_layout.setContentsMargins(0, 0, 0, 0)
    desc_layout.addLayout(state_layout)

    version_label = QLabel()
    version_label.setText(server_info.version.name)
    version_label.setAlignment(Qt.AlignLeft)
    state_layout.addWidget(version_label)

    host_port_label = QLabel()
    host_port_label.setText(f"{host}:{port}")
    host_port_label.setAlignment(Qt.AlignCenter)
    state_layout.addWidget(host_port_label)

    player_layout = QHBoxLayout()
    player_layout.setContentsMargins(0, 0, 0, 0)
    state_layout.addLayout(player_layout)

    player_label = QLabel()
    player_label.setText(f"{server_info.players.online}/{server_info.players.max}")
    player_label.setAlignment(Qt.AlignRight)
    player_layout.addWidget(player_label)

    @showException
    def _show_player_list(*_):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("玩家列表")

        html_space = "&nbsp;"

        player_html = "<span>"
        player_html += (
            f"<span>最大在线:{server_info.players.max}{html_space}"
            f"当前在线:{server_info.players.online}</span><br/>"
        )

        player_html += "<span>玩家列表:</span><br/>"

        if server_info.players.sample is not None:
            for player in server_info.players.sample:
                player_html += f"{html_space * 4}{player.name.to_html()}<br/>"
        player_html += "</span>"
        player_html = _html_add_background_color(
            (255, 255, 255),
            (180, 180, 180),
            player_html
        )
        player_html = _html_add_background_color(
            (255, 255, 85),
            (220, 220, 220),
            player_html
        )

        msg_box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, is_window_top())

        msg_box.setText(player_html)
        msg_box.exec()

    player_list_button = QPushButton()
    player_list_button.setStyleSheet(
        "QPushButton{border: 1px solid gray;"
        "background-color: rgb(230, 230, 230);"
        "padding: 4px;}"
    )
    player_list_button.setCursor(Qt.CursorShape.PointingHandCursor)
    player_list_button.setText("玩家列表")
    # noinspection PyUnresolvedReferences
    player_list_button.clicked.connect(_show_player_list)
    player_layout.addWidget(player_list_button)

    desc_label = QLabel()

    desc_html = ColorString.from_string(server_info.description.to_string()).to_html()
    desc_html = _html_add_background_color(
        (255, 255, 255),
        (220, 220, 220),
        desc_html
    )
    desc_html = _html_add_background_color(
        (255, 255, 85),
        (220, 220, 220),
        desc_html
    )
    desc_html = f"<span>{desc_html.replace('\n', "<br/>")}</span>"
    desc_label.setText(desc_html)
    desc_layout.addWidget(desc_label)

    return widget


@register
class ServerScan(AbcUI):
    def __init__(self, _parent: QTabWidget):
        super().__init__(_parent)

        self.widget: QWidget | None = None

        self.ip_input: QComboBox | None = None

        self.scan_button: CallbackPushButton | None = None
        self.show_log: LogListWidget | None = None

        self.result_count_label: QLabel | None = None

        self.progress_bar: QProgressBar | None = None

        self.scroll_area: QScrollArea | None = None
        self.scroll_area_widget: QWidget | None = None
        self.show_result_list: QListWidget | None = None

        self.show_advanced_settings: QCheckBox | None = None
        self.advanced_settings_widget: QWidget | None = None

        self.log_level_tip: QLabel | None = None
        self.enable_log_level_list: QListWidget | None = None
        self.add_log_level_combo: QComboBox | None = None
        self.add_log_level_btn: QPushButton | None = None

        self.port_input_tip: QLabel | None = None
        self.start_port_input: QSpinBox | None = None
        self.end_port_input: QSpinBox | None = None

        self.scan_timeout_tip: QLabel | None = None
        self.scan_connect_timeout_input: QDoubleSpinBox | None = None
        self.scan_parse_timeout_input: QDoubleSpinBox | None = None

        self.stop_scan_btn: QPushButton | None = None
        self.clean_log_btn: QPushButton | None = None
        self.auto_scroll_check_box: QCheckBox | None = None

        self.scan_connect_timeout = 0.9
        self.scan_parse_timeout = 1

        self.scanner: Scanner | None = None
        self.start_port, self.end_port = 1000, 65535

        self.result_ls: list[ServerInfo] = []

    def _is_window_top(self) -> bool:
        flags = self.widget.window().windowFlags() & Qt.WindowType.WindowStaysOnTopHint
        return flags == Qt.WindowType.WindowStaysOnTopHint

    @showException
    def _callback(self, event):
        def _parse_thread_finish(e: ThreadFinishEvent):
            try:
                parsed = json.loads(e.result[3:].decode())
            except Exception as err:
                self._log([e.port], f"解析失败 Error: {type(err).__name__}: {err}", LogLevel.WARNING)
                return

            self._log([e.port], f"存在服务器", LogLevel.DEBUG)

            server_info = ServerInfo(parsed)
            self.result_ls.append(server_info)
            self.result_count_label.setText(f"扫描结果: {len(self.result_ls)}")

            item = QListWidgetItem()
            item.setData(Qt.UserRole, (server_info, e.host, e.port))

            widget = _spawn_info_widget(server_info, e.host, e.port, is_window_top=self._is_window_top)

            item.setSizeHint(QSize(0, 64 + 15))

            self.show_result_list.addItem(item)
            self.show_result_list.setItemWidget(item, widget)

        def _parse_thread_error(e: ThreadErrorEvent):
            if type(e.error) is TimeoutError:
                return
            if type(e.error) is socket.gaierror:
                return
            self._log([e.port], f"意外的错误 {type(e.error).__name__}: {e.error}", LogLevel.ERROR)

        def _parse_start(e: StartEvent):
            len_port = len(e.port)
            self._log([e.host], f"开始扫描 共计{len_port}个端口")
            self.scan_button.setEnabled(False)
            self.ip_input.setEnabled(False)

            self.result_ls.clear()

            self.show_result_list.clear()

            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(len_port)
            self.progress_bar.setValue(0)
            self.progress_bar.setToolTip("正在扫描...")

            self.result_count_label.setText("正在扫描...")

        def _parse_finish(e: FinishEvent):
            message = ''
            message += f"扫描结束\n"
            message += f"共计{len(e.all_ports)}个端口\n"
            message += f"成功完成{len(e.finished_ports)}个端口\n"
            message += f"在{len(e.error_ports)}个端口上发生错误\n"
            message += f"总计用时{e.used_time_ns / 1000000000:.2f}秒"
            self._log([], message, LogLevel.INFO)
            self.result_count_label.setText(f"扫描结果: {len(self.result_ls)}")
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.progress_bar.setToolTip(f"扫描结束 共计{len(e.all_ports)}个端口")
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
        self._log([], f"初始化扫描器  起始端口: {self.start_port} 结束端口: {self.end_port}")
        self.scan_button.setEnabled(False)
        self.scan_button.setToolTip("正在扫描请勿重复操作...")
        self.ip_input.setEnabled(False)
        self.ip_input.setToolTip("正在扫描请勿重复操作...")

        def _emit(e: ABCEvent):
            # noinspection PyUnresolvedReferences
            self.scan_button.callback_signal.emit(e)

        self.scanner = Scanner(
            self.ip_input.currentText(),
            set(range(self.start_port, self.end_port + 1)),
            _emit,
            socket_reader=_read_packet,
            max_threads=256,
        )

        self._log(
            [],
            f"设置扫描超时  连接超时: {self.scan_connect_timeout}秒 解析超时: {self.scan_parse_timeout}秒"
        )
        self.scanner.connect_timeout = self.scan_connect_timeout
        self.scanner.scan_timeout = self.scan_connect_timeout + self.scan_parse_timeout

        def _start():
            self.scanner.start()
            self.stop_scan_btn.setEnabled(True)

        threading.Thread(target=_start, daemon=True, name="Start Scanner").start()

    @showException
    def _stop_scan(self, *_):
        self.stop_scan_btn.setEnabled(False)
        self._log([], "正在尝试终止扫描...")
        self.scanner.stop(wait=False)

    @showException
    def _showServerDetails(self, item: QListWidgetItem):
        index = self.show_result_list.indexFromItem(item)
        index: QModelIndex
        server_info = self.result_ls[index.row()]

        _, host, port = item.data(Qt.UserRole)

        html_space = "&nbsp;"

        description = ColorString.from_string(server_info.description.to_string()).to_html()
        description_list = description.split('\n')
        description_html = '\n'.join(
            [f"{html_space * 4}{line}" for line in description_list]
        )

        if server_info.players.sample is not None:
            player_list_str = "玩家列表:\n"
            for player in server_info.players.sample:
                player_list_str += f"{html_space * 4}{player.name.to_html()}{html_space}({player.id})\n"
            player_list_str += '\n'
        else:
            player_list_str = ''

        if server_info.forgeData is not None:
            mod_list_str = "服务端模组列表:\n"
            for mod in server_info.forgeData.mods:
                mod_list_str += f"{html_space * 4}{mod.modId}{html_space}({mod.modmarker})\n"
        else:
            mod_list_str = ''

        message = "<span>"
        message += f"服务器地址: {host}:{port}"
        message += f"服务端版本: {server_info.version.name}\n"
        message += f"服务器描述:\n{description_html}\n"
        message += f"在线玩家: {server_info.players.online}/{server_info.players.max}\n"
        message += player_list_str
        message += mod_list_str

        message += "</span>"
        message = message.replace("\n", "<br/>")

        message = _html_add_background_color(
            (255, 255, 255),
            (220, 220, 220),
            message,
        )
        message = _html_add_background_color(
            (255, 255, 85),
            (220, 220, 220),
            message,
        )

        msg_box = QMessageBox()
        msg_box.setWindowTitle("服务器详情")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Close)

        def _copy_server_address(*_):
            clipboard = QApplication.clipboard()
            clipboard.setText(f"{host}:{port}")

        copy_button = QPushButton("复制地址")
        # noinspection PyUnresolvedReferences
        copy_button.clicked.connect(_copy_server_address)

        msg_box.addButton(copy_button, QMessageBox.ButtonRole.ActionRole)

        msg_box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self._is_window_top())

        msg_box.exec()

    def _log(self, root: list[str] | list, text: str, level: LogLevel = LogLevel.INFO):
        self.show_log.log(root, text, level)

    @showException
    def _disable_log_level(self, item: QListWidgetItem):
        index = self.enable_log_level_list.row(item)
        self.enable_log_level_list.takeItem(index)

        self.show_log.disableLogLevels(LogLevel(item.text()))

        self.add_log_level_combo.addItem(item.text())

        self.add_log_level_combo.setVisible(True)
        self.add_log_level_btn.setVisible(True)

    @showException
    def _enable_log_level(self, *_):
        self.show_log.enableLogLevels(LogLevel(self.add_log_level_combo.currentText()))

        self.enable_log_level_list.clear()
        self.enable_log_level_list.addItems(self.show_log.enable_log_levels - NonUsable)

        self.add_log_level_combo.removeItem(self.add_log_level_combo.currentIndex())
        if self.add_log_level_combo.count() == 0:
            self.enable_log_level_list.setFocus()
            self.add_log_level_combo.setVisible(False)
            self.add_log_level_btn.setVisible(False)

    @showException
    def _show_advanced_settings(self, *_):
        self.advanced_settings_widget.setVisible(True)
        self.scroll_area.setFocus()

    @showException
    def _on_start_port_changed(self, new_value):
        if self.end_port_input.value() < new_value:
            self.end_port_input.setValue(new_value)
        self.start_port = new_value

    @showException
    def _on_end_port_changed(self, *_):
        if self.start_port_input.value() > self.end_port_input.value():
            self.start_port_input.setValue(self.end_port_input.value())
        self.end_port = self.end_port_input.value()

    @showException
    def _on_scan_connect_timeout_changed(self, new_value):
        dec_len = self.scan_connect_timeout_input.decimals()
        self.scan_connect_timeout = round(new_value, dec_len)

    @showException
    def _on_scan_parse_timeout_changed(self, new_value):
        dec_len = self.scan_parse_timeout_input.decimals()
        self.scan_parse_timeout = round(new_value, dec_len)

    @showException
    def _on_clear_btn(self, *_):
        self.show_log.clear()
        self.show_log.logAlways([], "MSS(Minecraft Server Scanner)测试版\nMade By: C418____11\n")

    @showException
    def _auto_scroll_type_changed(self, state):
        is_enable = bool(state)
        self.show_log.enable_auto_scroll = is_enable

    @override
    def setupUi(self):
        self.widget = QWidget(self._parent)
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

        self.result_count_label = QLabel("未进行过扫描", self.widget)
        self.result_count_label.setAlignment(Qt.AlignCenter)

        self.show_log = LogListWidget(self.widget)
        self.show_log.setToolTip("扫描日志")
        self.show_log.logAlways([], "MSS(Minecraft Server Scanner)测试版\nMade By: C418____11\n")
        self.show_log.setStyleSheet("background-color: rgba(255, 0, 0, 64);")

        self.progress_bar = QProgressBar(self.widget)
        self.progress_bar.setToolTip("未开始扫描")
        self.progress_bar.setMinimum(0)

        self.scroll_area = QScrollArea(self.widget)
        self.scroll_area_widget = QWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.show_result_list = QListWidget(self.scroll_area_widget)
        self.show_result_list.setToolTip("扫描结果")
        self.show_result_list.setStyleSheet("border: 0px")
        # noinspection PyUnresolvedReferences
        self.show_result_list.itemDoubleClicked.connect(self._showServerDetails)

        self.show_advanced_settings = QCheckBox("显示高级设置", self.scroll_area_widget)
        self.show_advanced_settings.setChecked(False)
        self.show_advanced_settings.setToolTip("显示高级设置")

        # noinspection PyUnresolvedReferences
        self.show_advanced_settings.clicked.connect(self._show_advanced_settings)

        self.advanced_settings_widget = QWidget(self.scroll_area_widget)
        self.advanced_settings_widget.hide()

        self.log_level_tip = QLabel("启用的日志级别", self.advanced_settings_widget)
        self.log_level_tip.setAlignment(Qt.AlignCenter)

        self.enable_log_level_list = QListWidget(self.advanced_settings_widget)
        self.enable_log_level_list.setToolTip("双击删除")
        self.enable_log_level_list.addItems(self.show_log.enable_log_levels - NonUsable)
        # noinspection PyUnresolvedReferences
        self.enable_log_level_list.itemDoubleClicked.connect(self._disable_log_level)

        self.add_log_level_combo = QComboBox(self.advanced_settings_widget)
        self.add_log_level_btn = QPushButton("添加", self.advanced_settings_widget)
        self.add_log_level_btn.hide()
        self.add_log_level_combo.hide()
        # noinspection PyUnresolvedReferences
        self.add_log_level_btn.clicked.connect(self._enable_log_level)

        self.port_input_tip = QLabel("端口范围", self.advanced_settings_widget)
        self.port_input_tip.setAlignment(Qt.AlignCenter)

        self.start_port_input = QSpinBox(self.advanced_settings_widget)
        self.start_port_input.setToolTip("*起始* 端口")
        self.start_port_input.setAlignment(Qt.AlignCenter)
        self.start_port_input.setMinimum(1)
        self.start_port_input.setMaximum(65535)
        self.start_port_input.setSingleStep(200)
        self.start_port_input.setValue(self.start_port)
        # noinspection PyUnresolvedReferences
        self.start_port_input.valueChanged.connect(self._on_start_port_changed)

        self.end_port_input = QSpinBox(self.advanced_settings_widget)
        self.end_port_input.setToolTip("*结束* 端口")
        self.end_port_input.setAlignment(Qt.AlignCenter)
        self.end_port_input.setMinimum(1)
        self.end_port_input.setMaximum(65535)
        self.end_port_input.setSingleStep(200)
        self.end_port_input.setValue(self.end_port)
        # noinspection PyUnresolvedReferences
        self.end_port_input.valueChanged.connect(self._on_end_port_changed)

        self.scan_timeout_tip = QLabel("扫描超时时限", self.advanced_settings_widget)
        self.scan_timeout_tip.setAlignment(Qt.AlignCenter)

        self.scan_connect_timeout_input = QDoubleSpinBox(self.advanced_settings_widget)
        self.scan_connect_timeout_input.setToolTip("扫描 *连接* 超时时限")
        self.scan_connect_timeout_input.setAlignment(Qt.AlignCenter)
        self.scan_connect_timeout_input.setDecimals(1)
        self.scan_connect_timeout_input.setMinimum(0.1)
        self.scan_connect_timeout_input.setMaximum(10)
        self.scan_connect_timeout_input.setSingleStep(0.1)
        self.scan_connect_timeout_input.setValue(self.scan_connect_timeout)
        self.scan_connect_timeout_input.setSuffix("秒")
        # noinspection PyUnresolvedReferences
        self.scan_connect_timeout_input.valueChanged.connect(self._on_scan_connect_timeout_changed)

        self.scan_parse_timeout_input = QDoubleSpinBox(self.advanced_settings_widget)
        self.scan_parse_timeout_input.setToolTip("扫描 *解析* 超时时限")
        self.scan_parse_timeout_input.setAlignment(Qt.AlignCenter)
        self.scan_parse_timeout_input.setDecimals(1)
        self.scan_parse_timeout_input.setMinimum(0.1)
        self.scan_parse_timeout_input.setMaximum(10)
        self.scan_parse_timeout_input.setSingleStep(0.1)
        self.scan_parse_timeout_input.setValue(self.scan_parse_timeout)
        self.scan_parse_timeout_input.setSuffix("秒")
        # noinspection PyUnresolvedReferences
        self.scan_parse_timeout_input.valueChanged.connect(self._on_scan_parse_timeout_changed)

        self.stop_scan_btn = QPushButton("终止扫描", self.advanced_settings_widget)
        self.stop_scan_btn.setToolTip("终止当前扫描任务")
        self.stop_scan_btn.setEnabled(False)
        # noinspection PyUnresolvedReferences
        self.stop_scan_btn.clicked.connect(self._stop_scan)

        self.clean_log_btn = QPushButton("清空日志", self.advanced_settings_widget)
        self.clean_log_btn.setToolTip("清空现存日志")
        # noinspection PyUnresolvedReferences
        self.clean_log_btn.clicked.connect(self._on_clear_btn)

        # 日志自动滚动切换按钮
        self.auto_scroll_check_box = QCheckBox("日志自动滚动", self.advanced_settings_widget)
        self.auto_scroll_check_box.setToolTip("切换日志自动滚动")
        # noinspection PyUnresolvedReferences
        self.auto_scroll_check_box.stateChanged.connect(self._auto_scroll_type_changed)
        self.auto_scroll_check_box.setChecked(True)

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

        self.progress_bar.resize(self.widget.width(), int(30 * y_scale))
        self.progress_bar.move(0, self.widget.height() - self.progress_bar.height())

        self.scroll_area.resize(self.widget.width(), int(0.5 * self.widget.height()))
        self.scroll_area.move(0, self.result_count_label.y() + self.result_count_label.height())
        self.scroll_area_widget.resize(self.scroll_area.width(), self.scroll_area.height() * 2)

        self.show_result_list.resize(
            self.widget.width() - self.scroll_area.verticalScrollBar().width() - 3,
            int(0.5 * self.widget.height())
        )
        self.show_advanced_settings.move(0, self.show_result_list.y() + self.show_result_list.height())

        self.advanced_settings_widget.move(0, self.show_advanced_settings.y())
        self.advanced_settings_widget.resize(self.widget.size())

        self.auto_scroll_check_box.resize(
            120,
            30
        )
        self.auto_scroll_check_box.move(
            self.advanced_settings_widget.width() - self.auto_scroll_check_box.width() -
            self.scroll_area.verticalScrollBar().width() - 3,
            0
        )

        self.log_level_tip.move(0, int(37 * y_scale))
        self.log_level_tip.resize(int(200 * x_scale), int(20 * y_scale))
        self.enable_log_level_list.move(0, self.log_level_tip.y() + self.log_level_tip.height() + 5)
        self.enable_log_level_list.resize(int(200 * x_scale), int(130 * y_scale))
        self.add_log_level_combo.move(0, self.enable_log_level_list.y() + self.enable_log_level_list.height() + 5)
        self.add_log_level_combo.resize(int(100 * x_scale), int(30 * y_scale))
        self.add_log_level_btn.move(
            self.add_log_level_combo.x() + self.add_log_level_combo.width(),
            self.enable_log_level_list.y() + self.enable_log_level_list.height() + 4
        )
        self.add_log_level_btn.resize(int(100 * x_scale), int(32 * y_scale))

        self.port_input_tip.move(
            self.log_level_tip.x() + self.log_level_tip.width() + int(10 * x_scale),
            int(37 * y_scale)
        )
        self.port_input_tip.resize(int(150 * x_scale), int(20 * y_scale))
        self.start_port_input.move(self.port_input_tip.x(), self.port_input_tip.y() + self.port_input_tip.height() + 5)
        self.start_port_input.resize(int(self.port_input_tip.width() / 2), int(30 * y_scale))
        self.end_port_input.move(self.start_port_input.x() + self.start_port_input.width(), self.start_port_input.y())
        self.end_port_input.resize(int(self.port_input_tip.width() / 2), int(30 * y_scale))

        self.scan_timeout_tip.move(
            self.port_input_tip.x(),
            self.end_port_input.y() + self.end_port_input.height() + int(10 * y_scale)
        )

        self.scan_timeout_tip.resize(int(150 * x_scale), int(20 * y_scale))
        self.scan_connect_timeout_input.move(
            self.scan_timeout_tip.x(),
            self.scan_timeout_tip.y() + self.scan_timeout_tip.height() + 5
        )
        self.scan_connect_timeout_input.resize(int(self.scan_timeout_tip.width() / 2), int(30 * y_scale))
        self.scan_parse_timeout_input.move(
            self.scan_connect_timeout_input.x() + self.scan_connect_timeout_input.width(),
            self.scan_connect_timeout_input.y()
        )
        self.scan_parse_timeout_input.resize(int(self.scan_timeout_tip.width() / 2), int(30 * y_scale))

        self.stop_scan_btn.move(
            self.port_input_tip.x() + self.port_input_tip.width() + int(30 * x_scale),
            self.port_input_tip.y()
        )
        self.stop_scan_btn.resize(int(200 * x_scale), int(30 * y_scale))
        self.clean_log_btn.move(
            self.stop_scan_btn.x(),
            self.stop_scan_btn.y() + self.stop_scan_btn.height() + int(10 * y_scale)
        )
        self.clean_log_btn.resize(int(200 * x_scale), int(30 * y_scale))

        self.show_log.resize(self.widget.width(), int(0.3 * self.widget.height()))
        self.show_log.move(0, self.progress_bar.y() - self.show_log.height())

    @override
    def getMainWidget(self):
        return self.widget

    @override
    def getTagName(self):
        return "服务器扫描"
