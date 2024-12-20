# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

from typing import Self


class OrderSet:
    """
    顺序集合
    """

    def __init__(self, _data_order: tuple[set, list] = None):
        if _data_order is not None:
            self.data = _data_order[0]
            self.order = _data_order[1]
        else:
            self.data = set()
            self.order = []

    def add(self, item):
        if item not in self:
            self.order.append(item)
        self.data.add(item)

    def remove(self, item):
        self.data.remove(item)
        self.order.remove(item)

    def clear(self):
        self.data.clear()
        self.order.clear()

    def update(self, item: Self):
        for item in item.data:
            if item not in self:
                self.order.append(item)
        self.data.update(item.data)

    def copy(self):
        return type(self)((self.data.copy(), self.order.copy()))

    def pop(self):
        ret = self.order.pop()
        self.data.remove(ret)
        return ret

    def sort(self, key=None, reverse=False):
        self.order.sort(key=key, reverse=reverse)

    def __repr__(self):
        return f"OrderSet({self.order})"

    def __iter__(self):
        return iter(self.order)

    def __len__(self):
        return len(self.data)

    def __contains__(self, item):
        return item in self.data

    def __getitem__(self, item):
        return self.order[item]

    def __setitem__(self, item, value):
        self.data.add(value)
        self.order[item] = value

    def __delitem__(self, item):
        self.data.remove(item)
        del self.order[item]


__all__ = ("OrderSet",)
