# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "MSS-0.0.8Dev"

import sys
import traceback

import colorama
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from tqdm import tqdm

import FeatureLoader
from GlobalConfigs import init as init_configs
from Lib.Config import DefaultConfigPool
from Lib.Config import requireConfig
from Lib.StdColor import ColorWrite
from UI import RegisterUI
from UI.Main import UiMain
from UI.tools import getDefaultImage

_load_other_futures = requireConfig(
    '', "FuturesLoad.yaml",
    {
        "Load": False,
    }
).checkConfig()


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor)
    app = QApplication(sys.argv)

    init_configs()

    FeatureLoader.load_default_features()

    if _load_other_futures.get("Load", False) is True:
        try:
            FeatureLoader.load_other_features()
        except Exception as e:
            print("An error occurred while loading another futures:", file=sys.stderr)
            traceback.print_exception(e)

    window = QMainWindow()

    # noinspection SpellCheckingInspection
    default_data = "Qk1GAAAAAAAAADYAAAAoAAAAAgAAAAIAAAABABgAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAA/wD/AAAAAAAAAAD/AP8AAA=="
    window.setWindowIcon(
        QIcon(
            getDefaultImage(
                "./Textures/icon.png",
                default_data
            ).scaled(
                16, 16,
                Qt.KeepAspectRatio
            )
        )
    )
    ui = UiMain(window)
    ui.setupUi()

    RegisterUI.menu.sort(key=lambda x: x.priority())
    RegisterUI.widgets.sort(key=lambda x: x.priority())

    _write = ColorWrite(sys.stdout, colorama.Fore.LIGHTCYAN_EX)

    for Menu in tqdm(RegisterUI.menu, leave=True, file=_write, desc="Registering menus", unit="Menu"):
        menu = Menu(ui.MenuBar, window)
        menu.setupUi()
        ui.MenuBar.addMenu(menu.getMenuWidget())

    for w in tqdm(RegisterUI.widgets, leave=True, file=_write, desc="Registering pages", unit="Page"):
        ui.append(w)

    # noinspection PyUnresolvedReferences
    window.setWindowFlags(Qt.CustomizeWindowHint)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    _green_write = ColorWrite(sys.stdout, colorama.Fore.LIGHTGREEN_EX)
    print(f"Core Version: {__version__}", file=_green_write)
    print(f"Core Author: {__author__}", file=_green_write)
    print(f"内核版本号: {__version__}", file=_green_write)
    print(f"内核作者: {__author__}", file=_green_write)
    DefaultConfigPool.saveAll()
    main()

__all__ = ("main",)
