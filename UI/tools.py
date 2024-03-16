# -*- coding: utf-8 -*-
# cython: language_level = 3

import os
import traceback
from functools import wraps
from typing import Union

from PyQt5.QtCore import QFileInfo
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFileIconProvider


def showException(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            traceback.print_exception(err)

    return wrapper


def fontFromPath(font_path, point_size=None):
    font_db = QFontDatabase()
    font_id = font_db.addApplicationFont(font_path)

    # 获取字体名称
    font_families = font_db.applicationFontFamilies(font_id)

    # 创建QFont对象
    font = QFont()
    font.setFamily(font_families[0])
    if point_size is not None:
        font.setPointSize(point_size)  # 设置字号
    return font


def ToFontMetrics(font: Union[QFont, QFontMetrics, str]):
    if isinstance(font, str):
        font = fontFromPath(font)
    if isinstance(font, QFont):
        font = QFontMetrics(font)
    if isinstance(font, QFontMetrics):
        fm = font
    else:
        # 抛出TypeError告诉调用者无法将font转换为QFontMetrics
        raise TypeError("font must be a QFont, QFontMetrics or str"
                        " but got {}".format(type(font)))
    return fm


def elidedText(text, font: Union[QFont, QFontMetrics, str], max_width, mode=Qt.ElideMiddle):
    fm = ToFontMetrics(font)
    return fm.elidedText(text, mode, max_width)


def getFileImage(
        file_path,
        size: Union[QSize, None],
        *,
        scaled_args=(Qt.KeepAspectRatio, Qt.SmoothTransformation)
) -> QPixmap:
    file_info = QFileInfo(file_path)
    icon_provider = QFileIconProvider()

    if size is None:
        size = QSize(32, 32)
    elif not isinstance(size, QSize):
        raise TypeError("size must be None or QSize")

    ext_name = os.path.splitext(file_path)[1].lower()

    if ext_name in (
            ".jpg", ".jpeg", ".png", ".bmp", ".gif", "ppm", ".tif", ".tiff", ".xbm", ".xpm"
    ):
        pixmap = QPixmap(file_path)
    else:
        pixmap = icon_provider.icon(file_info).pixmap(32)

    pixmap = pixmap.scaled(size, *scaled_args)
    return pixmap


def add_line_breaks(text: str, width: int, font_metrics: QFontMetrics):
    # 获取文本宽度
    def get_width(_text):
        return font_metrics.size(Qt.TextExpandTabs, _text).width()

    text_width = get_width(text)

    if text_width < width:
        return text
    result = ''

    chr_width = 0
    for sub_word in text:
        chr_width += get_width(sub_word)
        if chr_width < width:
            result += sub_word
        else:
            result += '\n' + sub_word
            chr_width = 0

    # 返回结果字符串
    return result


__all__ = ("showException", "fontFromPath", "ToFontMetrics", "elidedText", "getFileImage", "add_line_breaks")
