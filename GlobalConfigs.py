# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "MSS-0.0.2Alpha"

import os

from PyQt5.QtGui import QFontDatabase

from Lib.Config import ConfigData
from Lib.Config import requireConfig

_screen: ConfigData = requireConfig('', "Screen.yaml", {
    "MinimumSize": {
        "width": 680,
        "height": 520
    },
    "Default Font": {
        "family": "Arial",
        "Font Size": {
            "Tiny": 8,
            "Small": 10,
            "Normal": 12,
            "Large": 14,
            "Huge": 16,
            "Title": 20,
        }
    }
}).checkConfig()

try:
    MinimumSize = tuple(int(_screen["MinimumSize"][key]) for key in ("width", "height"))
except KeyError:
    MinimumSize = (680, 520)

_font = _screen.get("Default Font", ConfigData())
_font_size = _font.get("Font Size", ConfigData())

FontFamily = _font.get("family", "Arial")

TinyFont = _font_size.get("Tiny", 8)
SmallFont = _font_size.get("Small", 10)
NormalFont = _font_size.get("Normal", 12)
LargeFont = _font_size.get("Large", 14)
HugeFont = _font_size.get("Huge", 16)
TitleFont = _font_size.get("Title", 20)


def init():
    global FontFamily
    if os.path.exists(os.path.normpath(FontFamily)):
        _font_id = QFontDatabase.addApplicationFont(os.path.normpath(FontFamily))
        FontFamily = QFontDatabase.applicationFontFamilies(_font_id)[0]
