# -*- coding: utf-8 -*-
# cython: language_level = 3


__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.2Dev"

from Lib.OrderSet import OrderSet
from UI.ABC import AbcMenu
from UI.ABC import AbcUI

widgets: OrderSet = OrderSet()


def register(widget: type[AbcUI]):
    """
    Can be used as a decorator or a function call.
    """
    widgets.add(widget)
    return widget


menu: OrderSet = OrderSet()


def register_menu(menu_item: type[AbcMenu]):
    """
    Can be used as a decorator or a function call.
    """
    menu.add(menu_item)
    return menu_item


__all__ = ("widgets", "register", "menu", "register_menu",)
