# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.5Dev"

import json
import os
import socket
import sys
import threading
from typing import Callable
from typing import override

import colorama
from PIL import Image
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from Lib.Configs import BASE_PATH
from Lib.Configs import FontFamily
from Lib.Configs import NormalFont
from Lib.Configs import SmallFont
from Lib.Configs import read_default_yaml
from Lib.MinecraftColorString import ColorString
from Lib.ParseMCServerInfo import ServerInfo
from Lib.StdColor import ColorWrite
from MinecraftServerScanner.Events import ABCEvent
from MinecraftServerScanner.Events import FinishEvent
from MinecraftServerScanner.Events import StartEvent
from MinecraftServerScanner.Events import ThreadErrorEvent
from MinecraftServerScanner.Events import ThreadFinishEvent
from MinecraftServerScanner.Events import ThreadStartEvent
from MinecraftServerScanner.Scanner import Scanner
from UI.ABC import AbcUI
from UI.LogList import LogLevel
from UI.LogList import LogListWidget
from UI.RegisterUI import register
from UI.tools import getDefaultImage
from UI.tools import showException

# noinspection SpellCheckingInspection
_config_file = read_default_yaml(
    os.path.join(BASE_PATH, 'ScanServer.yaml'),
    {
        "DefaultServerIcon": "./Textures/DefaultServerIcon.png",
        "DefaultTarget": [
            "127.0.0.1",
            # "s2.wemc.cc",
            # "cl-sde-bgp-1.openfrp.top",
            # "cn-bj-bgp-2.openfrp.top",
            # "cn-bj-bgp-4.openfrp.top",
            # "cn-bj-plc-1.openfrp.top",
            # "cn-bj-plc-2.openfrp.top",
            # "cn-cq-plc-1.openfrp.top",
            # "cn-fz-plc-1.openfrp.top",
            # "cn-he-plc-1.openfrp.top",
            # "cn-he-plc-2.openfrp.top",
            # "cn-hk-bgp-4.openfrp.top",
            # "cn-hk-bgp-5.openfrp.top",
            # "cn-hk-bgp-6.openfrp.top",
            # "cn-hz-bgp-1.openfrp.top",
            # "cn-nd-plc-1.openfrp.top",
            # "cn-qz-plc-1.openfrp.top",
            # "cn-sc-plc-2.openfrp.top",
            # "cn-sy-dx-2.openfrp.top",
            # "cn-sz-bgp-1.openfrp.top",
            # "cn-sz-plc-1.openfrp.top",
            # "cn-wh-plc-1.openfrp.top",
            # "cn-yw-plc-1.openfrp.top",
            # "jp-osk-bgp-1.openfrp.top",
            # "kr-nc-bgp-1.openfrp.top",
            # "kr-se-cncn-1.openfrp.top",
            # "ru-mow-bgp-1.openfrp.top",
            # "us-sjc-bgp-1.openfrp.top",
            # "us-sjc-bgp-2.openfrp.top"
        ]
    })


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


def _spawn_info_widget(server_info: ServerInfo, host: str, port: int, *, is_window_top: Callable[[], bool]) -> QWidget:
    widget = QWidget()
    widget.setToolTip("双击显示详细信息")
    root_layout = QHBoxLayout()
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)
    widget.setLayout(root_layout)

    icon_path = _config_file.get_default("DefaultServerIcon", None)
    # noinspection SpellCheckingInspection
    default_data = "Qk1GAAAAAAAAADYAAAAoAAAAAgAAAAIAAAABABgAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAA/wD/AAAAAAAAAAD/AP8AAA=="
    pixmap = getDefaultImage(
        icon_path,
        default_data
    )
    if server_info.favicon is not None:
        image_bytes = server_info.favicon.to_bytes()
        pixmap.loadFromData(image_bytes)

    image_label = QLabel()
    pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio)
    image_label.setPixmap(pixmap)
    image_label.setFixedSize(QSize(64, 64))
    root_layout.addWidget(image_label)

    details_layout = QVBoxLayout()
    details_layout.setContentsMargins(0, 0, 0, 0)
    details_layout.setSpacing(0)
    root_layout.addLayout(details_layout)

    info_layout = QHBoxLayout()
    info_layout.setContentsMargins(0, 0, 0, 0)
    info_layout.setSpacing(0)
    details_layout.addLayout(info_layout)

    version_label = QLabel()
    version_label.setText(server_info.version.name)
    version_label.setAlignment(Qt.AlignLeft)
    info_layout.addWidget(version_label)

    host_port_label = QLabel()
    host_port_label.setText(f"{host}:{port}")
    host_port_label.setAlignment(Qt.AlignCenter)
    info_layout.addWidget(host_port_label, Qt.AlignCenter)

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

    player_label = QPushButton()
    player_label.setText(f"{server_info.players.online}/{server_info.players.max}")
    # noinspection PyUnresolvedReferences
    player_label.clicked.connect(_show_player_list)
    info_layout.addWidget(player_label)

    desc_layout = QVBoxLayout()
    desc_layout.setContentsMargins(0, 0, 0, 0)
    desc_layout.setSpacing(0)
    details_layout.addLayout(desc_layout)

    desc_label = QLabel()
    desc_html = server_info.description.to_html()
    desc_html = "<span>" + desc_html.replace('\n', "<br/>") + "</span>"
    desc_label.setText(desc_html)
    desc_layout.addWidget(desc_label)

    return widget


@register
class ServerScan(AbcUI):
    def __init__(self, _parent: QTabWidget, *_):
        super().__init__(_parent, None)

        self.widget: QWidget | None = None

        self.input_area: QWidget | None = None
        self.ip_input: QComboBox | None = None
        self.scan_button: CallbackPushButton | None = None

        self.show_result_list: QListWidget | None = None
        self.result_count_label: QLabel | None = None

        self.show_log: LogListWidget | None = None
        self.progress_bar: QProgressBar | None = None

        self.scanner: Scanner | None = None
        self.start_port, self.end_port = 1000, 65535

        self.max_threads = 256

        self.scan_connect_timeout = 0.9
        self.scan_parse_timeout = 1

    def _is_window_top(self) -> bool:
        flags = self.widget.window().windowFlags() & Qt.WindowType.WindowStaysOnTopHint
        return flags == Qt.WindowType.WindowStaysOnTopHint

    @showException
    def _callback(self, event):
        def _parse_thread_finish(e: ThreadFinishEvent):
            try:
                parsed = json.loads(e.result[3:].decode())
            except Exception as err:
                self.log([e.port], f"解析失败 Error: {type(err).__name__}: {err}", LogLevel.WARNING)
                return

            self.log([e.port], f"存在服务器", LogLevel.DEBUG)

            server_info = ServerInfo(parsed)
            self.result_count_label.setText(f"扫描结果: {self.show_result_list.count()}")

            item = QListWidgetItem()
            item.setData(Qt.UserRole, (server_info, e.host, e.port))

            widget = _spawn_info_widget(server_info, e.host, e.port, is_window_top=self._is_window_top)

            item.setSizeHint(QSize(0, 64))

            self.show_result_list.addItem(item)
            self.show_result_list.setItemWidget(item, widget)

        def _parse_thread_error(e: ThreadErrorEvent):
            if type(e.error) is TimeoutError:
                return
            if type(e.error) is socket.gaierror:
                return
            self.log([e.port], f"意外的错误 {type(e.error).__name__}: {e.error}", LogLevel.ERROR)

        def _parse_start(e: StartEvent):
            len_port = len(e.port)
            self.log([e.host], f"开始扫描 共计{len_port}个端口")
            self.scan_button.setEnabled(False)
            self.ip_input.setEnabled(False)

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
            self.log([], message, LogLevel.INFO)
            self.result_count_label.setText(f"扫描结果: {self.show_result_list.count()}")
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.progress_bar.setToolTip(f"扫描结束 共计{len(e.all_ports)}个端口")
            self.scan_button.setEnabled(True)
            self.ip_input.setEnabled(True)
            self.scan_button.setToolTip("点击开始")
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
        self.log([],
                 f"初始化扫描器  起始端口: {self.start_port} 结束端口: {self.end_port} 最大并发量: {self.max_threads}")
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
            max_threads=self.max_threads,
        )

        self.log([], f"设置扫描超时  连接超时: {self.scan_connect_timeout}秒 解析超时: {self.scan_parse_timeout}秒")
        self.scanner.connect_timeout = self.scan_connect_timeout
        self.scanner.scan_timeout = self.scan_connect_timeout + self.scan_parse_timeout

        threading.Thread(target=self.scanner.start, daemon=True, name="Start Scanner").start()

    @showException
    def _showServerDetails(self, item: QListWidgetItem):
        server_info, host, port = item.data(Qt.UserRole)

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

        @showException
        def _export(*_):
            try:
                if not os.path.exists("./.export"):
                    os.makedirs("./.export", exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self.widget, "提示", f"未能创建输出文件夹\n{type(e)}:\n{e}")

            file_path, _ = QFileDialog.getSaveFileName(
                caption="导出",
                directory="./.export/RawServerData.json",
                filter="All Files (*);;Json Files (*.json);;Text Files (*.txt)",
                initialFilter="Json Files (*.json)",
            )
            if not file_path:
                return

            data = {
                "host": host,
                "port": port,
                "data": server_info.raw_data
            }
            try:
                with open(file_path, mode="w", encoding="utf-8") as f:
                    json.dump(data, f, sort_keys=True, indent=2)
            except Exception as e:
                QMessageBox.critical(self.widget, "警告", f"导出失败\n{type(e)}:\n{e}")
                raise

        export_button = QPushButton("导出数据")
        # noinspection PyUnresolvedReferences
        export_button.clicked.connect(_export)
        msg_box.addButton(export_button, QMessageBox.ButtonRole.ActionRole)

        @showException
        def _copy_server_address(*_):
            clipboard = QApplication.clipboard()
            clipboard.setText(f"{host}:{port}")

        copy_button = QPushButton("复制地址")
        # noinspection PyUnresolvedReferences
        copy_button.clicked.connect(_copy_server_address)
        msg_box.addButton(copy_button, QMessageBox.ButtonRole.ActionRole)

        @showException
        def _save_server_favicon(*_):
            image: Image.Image = server_info.favicon.to_image()
            base_filename = f"{host}[{port}].png"
            filename = QFileDialog.getSaveFileName(
                None,
                "保存图标",
                base_filename,
                "PNG图片 (*.png);;JPG图片 (*.jpg);;所有文件 (*)"

            )[0]

            if not filename:
                return

            image.save(filename)

        save_button = QPushButton("保存图标")
        # noinspection PyUnresolvedReferences
        save_button.clicked.connect(_save_server_favicon)
        msg_box.addButton(save_button, QMessageBox.ButtonRole.ActionRole)

        msg_box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self._is_window_top())
        msg_box.exec()

    def log(self, root: list[str] | list, text: str, level: LogLevel = LogLevel.INFO):
        self.show_log.log(root, text, level)

    @override
    def setupUi(self):
        self.widget = QWidget(self._parent)

        self.input_area = QWidget(self.widget)
        self.ip_input = QComboBox(self.input_area)
        self.ip_input.setEditable(True)
        self.ip_input.addItems(_config_file["DefaultTarget"])
        self.scan_button = CallbackPushButton(self.input_area)

        self.result_count_label = QLabel(self.widget)
        self.result_count_label.setAlignment(Qt.AlignCenter)

        self.show_log = LogListWidget(self.widget)
        self.show_log.setStyleSheet("background-color: rgba(255, 0, 0, 64);")
        self.show_log.setAutoScroll(True)
        self.progress_bar = QProgressBar(self.widget)
        self.progress_bar.setMinimum(0)

        self.show_result_list = QListWidget(self.widget)

        if os.path.exists("./Textures/light_dirt_background.png"):
            self.widget.setStyleSheet(
                "QWidget{"
                "  background: url(./Textures/light_dirt_background.png);"
                "  color: white;"
                "};"
            )
            self.ip_input.setStyleSheet(
                "color: default;"
                "background: none"
            )

        self.widget.setLayout(QVBoxLayout())
        self.widget.layout().setContentsMargins(0, 0, 0, 0)
        self.widget.layout().setSpacing(0)
        self.widget.layout().addWidget(self.input_area)
        self.widget.layout().addWidget(self.result_count_label)
        self.widget.layout().addWidget(self.show_result_list)
        self.widget.layout().setStretch(2, 2)
        self.widget.layout().addWidget(self.show_log)
        self.widget.layout().setStretch(3, 1)
        self.widget.layout().addWidget(self.progress_bar)
        self.input_area.setLayout(QHBoxLayout())
        self.input_area.layout().setContentsMargins(0, 0, 0, 0)
        self.input_area.layout().setSpacing(0)
        self.input_area.layout().addWidget(self.ip_input)
        self.input_area.layout().setStretch(0, 3)
        self.input_area.layout().addWidget(self.scan_button)
        self.input_area.layout().setStretch(1, 1)

        self.reSetFont()
        self.reTranslate()

        # noinspection PyUnresolvedReferences
        self.scan_button.clicked.connect(self._start_scan)
        # noinspection PyUnresolvedReferences
        self.scan_button.callback_signal.connect(self._callback)
        # noinspection PyUnresolvedReferences
        self.show_result_list.itemDoubleClicked.connect(self._showServerDetails)

    def reTranslate(self):
        self.ip_input.lineEdit().setPlaceholderText("IP地址或域名...")
        self.ip_input.lineEdit().setAlignment(Qt.AlignCenter)

        self.scan_button.setText("扫描")
        self.scan_button.setToolTip("点击开始")

        self.result_count_label.setText("未进行过扫描")
        self.show_result_list.setToolTip("扫描结果")

        self.show_log.setToolTip("扫描日志")
        self.show_log.logAlways([], "MSS(Minecraft Server Scanner)测试版\nMade By: C418____11\n")
        self.progress_bar.setToolTip("未开始扫描")

    def reSetFont(self):
        norm_font = QFont(FontFamily, NormalFont)
        self.ip_input.setFont(norm_font)
        self.ip_input.lineEdit().setFont(norm_font)
        self.scan_button.setFont(norm_font)
        self.result_count_label.setFont(norm_font)
        self.show_log.setFont(QFont(FontFamily, SmallFont))

    @override
    def getMainWidget(self):
        return self.widget

    @override
    def getTagName(self):
        return "服务器扫描"

    @override
    def exit(self):
        if self.scanner is None:
            return
        light_magenta = ColorWrite(sys.stdout, colorama.Fore.LIGHTMAGENTA_EX)
        print("Stopping Scanner...", file=light_magenta)
        self.scanner.stop()
        print("Scanner Stopped", file=light_magenta)
