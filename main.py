# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.7Dev"

import os
import sys
import traceback

import colorama
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from tqdm import tqdm

import FeatureLoader
from Lib.Configs import BASE_PATH
from Lib.Configs import read_default_yaml
from Lib.StdColor import ColorWrite
from UI import RegisterUI
from UI.BaseWidgets import GetScale
from UI.Main import UiMain

_load_other_futures = read_default_yaml(
    os.path.join(BASE_PATH, 'FuturesLoad.yaml'),
    {
        "Load": True,
    }
)


def main():
    FeatureLoader.load_default_features()

    if _load_other_futures.get_default("Load", False) is True:
        try:
            FeatureLoader.load_other_features()
        except Exception as e:
            print("An error occurred while loading another futures:", file=sys.stderr)
            traceback.print_exception(e)

    app = QApplication(sys.argv)
    widget = GetScale()
    ui = UiMain(widget)
    ui.setupUi()

    RegisterUI.menu.sort(key=lambda x: x.priority())
    RegisterUI.widgets.sort(key=lambda x: x.priority())

    _write = ColorWrite(sys.stdout, colorama.Fore.LIGHTCYAN_EX)

    for Menu in tqdm(RegisterUI.menu, leave=True, file=_write, desc="Registering menus", unit="Menu"):
        menu = Menu(ui.MenuBar, widget)
        menu.setupUi()
        ui.MenuBar.addMenu(menu.getMenuWidget())

    for w in tqdm(RegisterUI.widgets, leave=True, file=_write, desc="Registering pages", unit="Page"):
        ui.append(w)

    # noinspection PyUnresolvedReferences
    widget.setWindowFlags(Qt.CustomizeWindowHint)
    widget.show()

    if len(ui.top_tabs) > 0 and hasattr(ui.top_tabs[0], "ReScale"):
        ui.top_tabs[0].ReScale(widget.scaleWidth, widget.scaleHeight)

    sys.exit(app.exec_())


if __name__ == "__main__":
    _green_write = ColorWrite(sys.stdout, colorama.Fore.LIGHTGREEN_EX)
    print(f"Version: {__version__}", file=_green_write)
    print(f"Author: {__author__}", file=_green_write)
    print(f"版本号: {__version__}", file=_green_write)
    print(f"作者: {__author__}", file=_green_write)
    main()

__all__ = ("main",)
