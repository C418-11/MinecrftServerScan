# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.2Dev"

import json
import os
import traceback
from typing import Union, override, Any

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from Lib.ParseMCServerInfo import ServerInfo
from MinecraftServerScanner.Events import ABCEvent
from MinecraftServerScanner.Events import StartEvent
from MinecraftServerScanner.Events import FinishEvent
from UI.RangedSpin import RangedSpinBox
from UI.Main import UiMain
from DefaultFeatures.ScanServer import ServerScan
from DefaultFeatures.ScanServer import _spawn_info_widget
from UI.ABC import AbcUI
from UI.LogList import LogLevel
from UI.LogList import NonUsable
from UI.RegisterUI import register
from UI.tools import showException


@register
class ScanSettings(AbcUI):
    _main_ui: UiMain

    def __init__(self, _parent: QTabWidget, _main_ui: UiMain):
        super().__init__(_parent, _main_ui)

        self.target_page: Union[ServerScan, None] = None
        self.widget: QWidget | None = None
        self.layout: QGridLayout | None = None

        self.log_level_label: QLabel | None = None
        self.enable_log_level_list: QListWidget | None = None
        self.add_log_level_combo: QComboBox | None = None
        self.add_log_level_btn: QPushButton | None = None

        self.port_input_label: QLabel | None = None
        self.port_input: RangedSpinBox | None = None

        self.scan_timeout_label: QLabel | None = None
        self.scan_connect_timeout_input: QDoubleSpinBox | None = None
        self.scan_parse_timeout_input: QDoubleSpinBox | None = None

        self.max_threads_label: QLabel | None = None
        self.max_threads_input: QSpinBox | None = None

        self.stop_scan_btn: QPushButton | None = None
        self.clean_log_btn: QPushButton | None = None
        self.import_export_label: QLabel | None = None
        self.import_btn: QPushButton | None = None
        self.export_btn: QPushButton | None = None
        self.auto_scroll_check_box: QCheckBox | None = None

    @showException
    def _disable_log_level(self, item: QListWidgetItem):
        index = self.enable_log_level_list.row(item)
        self.enable_log_level_list.takeItem(index)

        self.target_page.show_log.disableLogLevels(LogLevel(item.text()))

        self.add_log_level_combo.addItem(item.text())

        self.add_log_level_combo.setVisible(True)
        self.add_log_level_btn.setVisible(True)

    @showException
    def _enable_log_level(self, *_):
        self.target_page.show_log.enableLogLevels(LogLevel(self.add_log_level_combo.currentText()))

        self.enable_log_level_list.clear()
        self.enable_log_level_list.addItems(self.target_page.show_log.enable_log_levels - NonUsable)

        self.add_log_level_combo.removeItem(self.add_log_level_combo.currentIndex())
        if self.add_log_level_combo.count() == 0:
            self.enable_log_level_list.setFocus()
            self.add_log_level_combo.setVisible(False)
            self.add_log_level_btn.setVisible(False)

    @showException
    def _on_scan_connect_timeout_changed(self, new_value):
        dec_len = self.scan_connect_timeout_input.decimals()
        self.target_page.scan_connect_timeout = round(new_value, dec_len)

    @showException
    def _on_scan_parse_timeout_changed(self, new_value):
        dec_len = self.scan_parse_timeout_input.decimals()
        self.target_page.scan_parse_timeout = round(new_value, dec_len)

    @showException
    def _on_max_threads_changed(self, new_value):
        self.target_page.max_threads = new_value

    @showException
    def _on_clear_btn(self, *_):
        self.target_page.show_log.clear()
        self.target_page.show_log.logAlways([], "MSS(Minecraft Server Scanner)测试版\nMade By: C418____11\n")

    @showException
    def _auto_scroll_type_changed(self, state):
        is_enable = bool(state)
        self.target_page.show_log.enable_auto_scroll = is_enable

    @showException
    def _callback(self, event: ABCEvent):
        if isinstance(event, StartEvent):
            self.stop_scan_btn.setEnabled(True)
        elif isinstance(event, FinishEvent):
            self.stop_scan_btn.setEnabled(False)

    @showException
    def _stop_scan(self, *_):
        total_timeout = self.scan_connect_timeout_input.value() + self.scan_parse_timeout_input.value()
        self.target_page.log([], f"正在尝试终止扫描... (约{total_timeout}秒后终止完成)")
        self.target_page.scanner.stop(wait=False)

    @showException
    def _on_port_changed(self, minimum: int, maximum: int):
        self.target_page.start_port = minimum
        self.target_page.end_port = maximum

    @showException
    def _on_import(self, *_):
        self.import_btn.setEnabled(False)
        file_path, _ = QFileDialog.getOpenFileName(
            caption="导入",
            directory="./.export/",
            filter="All Files (*);;Json Files (*.json);;Text Files (*.txt)",
            initialFilter="Json Files (*.json)",
        )

        if not file_path:
            self.import_btn.setEnabled(True)
            return

        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                try:
                    servers = json.load(f)
                except json.JSONDecodeError:
                    QMessageBox.critical(self.widget, "警告", "损坏的文件")
                    self.import_btn.setEnabled(True)
                    return
        except Exception as e:
            QMessageBox.critical(self.widget, "警告", f"导入失败\n{type(e)}:\n{e}")
            self.import_btn.setEnabled(True)
            raise

        if isinstance(servers, dict):
            servers = [servers]
        elif not isinstance(servers, list):
            QMessageBox.critical(self.widget, "警告", "损坏的文件")
            self.import_btn.setEnabled(True)
            return

        widgets: list[QListWidgetItem] = []
        processed_server_ls: list[tuple[ServerInfo, str, int]] = []
        for data in servers:
            server_info = ServerInfo(data["data"])
            host = data["host"]
            port = data["port"]
            processed_server_ls.append((server_info, host, port))

            try:
                # noinspection PyProtectedMember
                widgets.append(_spawn_info_widget(
                    server_info, host, port,
                    is_window_top=self.target_page._is_window_top
                ))
            except Exception as e:
                traceback.print_exception(e)
                QMessageBox.critical(self.widget, "警告", f"导入失败\n{type(e)}:\n{e}")
                self.import_btn.setEnabled(True)
                return
            QApplication.processEvents()

        result_list = self.target_page.show_result_list
        result_list.clear()
        for widget, (server_info, host, port) in zip(widgets, processed_server_ls):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, (server_info, host, port))
            item.setSizeHint(QSize(0, 64))

            result_list.addItem(item)
            result_list.setItemWidget(item, widget)
            QApplication.processEvents()

        self.import_btn.setEnabled(True)
        self._main_ui.TopTab.setCurrentIndex(self._main_ui.TopTab.indexOf(self.target_page.getMainWidget()))

    @showException
    def _on_export(self, *_):
        try:
            if not os.path.exists("./.export"):
                os.makedirs("./.export", exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self.widget, "提示", f"未能创建输出文件夹\n{type(e)}:\n{e}")

        file_path, _ = QFileDialog.getSaveFileName(
            caption="导出",
            directory="./.export/MinecraftServers.json",
            filter="All Files (*);;Json Files (*.json);;Text Files (*.txt)",
            initialFilter="Json Files (*.json)",
        )
        result_list = self.target_page.show_result_list

        if not file_path:
            return

        results: list[dict[str, Any]] = []
        for x in range(result_list.count()):
            data = result_list.item(x).data(Qt.UserRole)
            server_info: ServerInfo = data[0]
            host: str = data[1]
            port: int = data[2]
            results.append({
                "host": host,
                "port": port,
                "data": server_info.raw_data
            })

        try:
            with open(file_path, mode="w", encoding="utf-8") as f:
                json.dump(results, f, sort_keys=True, indent=2)
        except Exception as e:
            QMessageBox.critical(self.widget, "警告", f"导出失败\n{type(e)}:\n{e}")
            raise

    @override
    def setupUi(self):
        self.widget = QWidget()
        self.target_page = [x for x in self._main_ui.top_tabs if isinstance(x, ServerScan)][0]

        self.log_level_label = QLabel(self.widget)
        self.log_level_label.setAlignment(Qt.AlignCenter)
        self.enable_log_level_list = QListWidget(self.widget)
        self.enable_log_level_list.addItems(self.target_page.show_log.enable_log_levels - NonUsable)
        self.add_log_level_combo = QComboBox(self.widget)
        self.add_log_level_btn = QPushButton(self.widget)
        self.add_log_level_btn.hide()
        self.add_log_level_combo.hide()

        self.port_input_label = QLabel(self.widget)
        self.port_input_label.setAlignment(Qt.AlignCenter)
        self.port_input = RangedSpinBox(self.widget)
        self.port_input.setRange(1, 65535)
        self.port_input.setSingleStep(200)
        self.port_input.setValue(self.target_page.start_port, self.target_page.end_port)
        self.port_input.setAlignment(Qt.AlignCenter)

        self.scan_timeout_label = QLabel(self.widget)
        self.scan_timeout_label.setAlignment(Qt.AlignCenter)
        self.scan_connect_timeout_input = QDoubleSpinBox(self.widget)
        self.scan_connect_timeout_input.setAlignment(Qt.AlignCenter)
        self.scan_connect_timeout_input.setDecimals(1)
        self.scan_connect_timeout_input.setMinimum(0.1)
        self.scan_connect_timeout_input.setMaximum(10)
        self.scan_connect_timeout_input.setSingleStep(0.1)
        self.scan_connect_timeout_input.setValue(self.target_page.scan_connect_timeout)
        self.scan_parse_timeout_input = QDoubleSpinBox(self.widget)
        self.scan_parse_timeout_input.setAlignment(Qt.AlignCenter)
        self.scan_parse_timeout_input.setDecimals(1)
        self.scan_parse_timeout_input.setMinimum(0.1)
        self.scan_parse_timeout_input.setMaximum(10)
        self.scan_parse_timeout_input.setSingleStep(0.1)
        self.scan_parse_timeout_input.setValue(self.target_page.scan_parse_timeout)

        self.max_threads_label = QLabel(self.widget)
        self.max_threads_label.setAlignment(Qt.AlignCenter)
        self.max_threads_input = QSpinBox(self.widget)
        self.max_threads_input.setAlignment(Qt.AlignCenter)
        self.max_threads_input.setMinimum(1)
        self.max_threads_input.setMaximum(512)
        self.max_threads_input.setSingleStep(8)
        self.max_threads_input.setValue(self.target_page.max_threads)

        self.stop_scan_btn = QPushButton(self.widget)
        self.stop_scan_btn.setEnabled(False)
        self.clean_log_btn = QPushButton(self.widget)
        self.import_export_label = QLabel(self.widget)
        self.import_export_label.setAlignment(Qt.AlignCenter)
        self.import_btn = QPushButton(self.widget)
        self.export_btn = QPushButton(self.widget)
        self.auto_scroll_check_box = QCheckBox(self.widget)
        self.auto_scroll_check_box.setChecked(True)

        t = QHBoxLayout()
        t.setContentsMargins(*[100] * 4)
        self.widget.setLayout(t)

        t = QVBoxLayout()
        self.widget.layout().addLayout(t)
        t.addWidget(self.log_level_label)
        t.addWidget(self.enable_log_level_list)
        u = QHBoxLayout()
        t.addLayout(u)
        t = u
        t.addWidget(self.add_log_level_combo)
        t.setStretch(0, 2)
        t.addWidget(self.add_log_level_btn)
        t.setStretch(1, 1)

        t = QVBoxLayout()
        self.widget.layout().addLayout(t)
        t.addWidget(self.port_input_label)
        t.addWidget(self.port_input)
        t.addWidget(self.scan_timeout_label)
        u = QHBoxLayout()
        t.addLayout(u)
        u.addWidget(self.scan_connect_timeout_input)
        u.addWidget(self.scan_parse_timeout_input)
        t.addWidget(self.max_threads_label)
        t.addWidget(self.max_threads_input)

        t = QVBoxLayout()
        self.widget.layout().addLayout(t)
        t.addWidget(self.stop_scan_btn)
        t.addWidget(self.clean_log_btn)
        t.addWidget(self.import_export_label)
        u = QHBoxLayout()
        t.addLayout(u)
        u.addWidget(self.import_btn)
        u.addWidget(self.export_btn)
        t.addWidget(self.auto_scroll_check_box)

        self.widget.layout().setStretch(0, 1)
        self.widget.layout().setStretch(1, 1)
        self.widget.layout().setStretch(2, 1)

        self.reTranslate()

        self.target_page.scan_button.callback_signal.connect(self._callback)
        # noinspection PyUnresolvedReferences
        self.enable_log_level_list.itemDoubleClicked.connect(self._disable_log_level)
        # noinspection PyUnresolvedReferences
        self.add_log_level_btn.clicked.connect(self._enable_log_level)
        # noinspection PyUsersolvedReferences
        self.port_input.valueChanged.connect(self._on_port_changed)
        # noinspection PyUnresolvedReferences
        self.scan_connect_timeout_input.valueChanged.connect(self._on_scan_connect_timeout_changed)
        # noinspection PyUnresolvedReferences
        self.scan_parse_timeout_input.valueChanged.connect(self._on_scan_parse_timeout_changed)
        # noinspection PyUnresolvedReferences
        self.max_threads_input.valueChanged.connect(self._on_max_threads_changed)
        # noinspection PyUnresolvedReferences
        self.stop_scan_btn.clicked.connect(self._stop_scan)
        # noinspection PyUnresolvedReferences
        self.clean_log_btn.clicked.connect(self._on_clear_btn)
        # noinspection PyUnresolvedReferences
        self.import_btn.clicked.connect(self._on_import)
        # noinspection PyUnresolvedReferences
        self.export_btn.clicked.connect(self._on_export)
        # noinspection PyUnresolvedReferences
        self.auto_scroll_check_box.stateChanged.connect(self._auto_scroll_type_changed)

    @override
    def reTranslate(self):
        self.log_level_label.setText("启用的日志级别")
        self.enable_log_level_list.setToolTip("双击删除")
        self.add_log_level_btn.setText("添加")
        self.add_log_level_btn.setToolTip("添加")

        self.port_input_label.setText("端口范围")
        self.port_input.minimumSpinBox().setToolTip("*起始* 端口")
        self.port_input.maximumSpinBox().setToolTip("*结束* 端口")
        self.scan_timeout_label.setText("扫描超时时限")
        self.scan_connect_timeout_input.setToolTip("扫描 *连接* 超时时限")
        self.scan_connect_timeout_input.setSuffix("秒")
        self.scan_parse_timeout_input.setToolTip("扫描 *解析* 超时时限")
        self.scan_parse_timeout_input.setSuffix("秒")
        self.max_threads_label.setText("最大线程数")
        self.max_threads_input.setToolTip("最大线程数")

        self.stop_scan_btn.setText("终止扫描")
        self.stop_scan_btn.setToolTip("终止当前扫描任务")
        self.clean_log_btn.setText("清空日志")
        self.clean_log_btn.setToolTip("清空现存日志")
        self.import_export_label.setText("导入/导出服务器列表")
        self.import_export_label.setMaximumHeight(self.import_export_label.sizeHint().height())
        self.import_btn.setText("导入")
        self.import_btn.setToolTip("*导入* 服务器列表")
        self.export_btn.setText("导出")
        self.export_btn.setToolTip("*导出* 服务器列表")
        self.auto_scroll_check_box.setText("日志自动滚动")
        self.auto_scroll_check_box.setToolTip("切换日志自动滚动")

    @override
    def getMainWidget(self):
        return self.widget

    @override
    def getTagName(self):
        return "扫描器高级选项"
