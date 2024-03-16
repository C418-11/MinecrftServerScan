# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.2Alpha"

import os
from collections import OrderedDict

import yaml


def read_default_yaml(path: str, default_config):
    if not os.path.exists(path):
        with open(path, 'w') as f:
            yaml.safe_dump(default_config, f)
    with open(path, 'r') as f:
        return Config(yaml.safe_load(f), file_path=path)


BASE_PATH = './.configs/'
if not os.path.exists(BASE_PATH):
    os.makedirs(BASE_PATH)


class Config:
    def __init__(
            self,
            config,
            path_from_root: list | None = None,
            file_path: str | None = None
    ):

        self.isNone = False
        if config is None:
            self.isNone = True
            config = {}
        if type(config) is dict:
            config = OrderedDict(config)

        if path_from_root is None:
            path_from_root = []

        self._config = config
        self._path_from_root = path_from_root
        self._file_path = file_path

        for key in self._config:
            if hasattr(self, key):
                raise KeyError(f"'{key}' is a reserved keyword")

    def get_default(self, key, default):
        if key in self:
            return self[key]
        return default

    @property
    def raw_config(self):
        return self._config

    def _key_not_found_message_box(self, key):
        path_str = ' -> '.join(self._path_from_root + [key])
        from tkinter import messagebox
        messagebox.showerror(
            "Error",
            f"Cannot find key {path_str} in configuration file {self._file_path}",
        )

    def sort(self, key=None, reverse: bool = False):
        if type(self._config) is OrderedDict:
            self._config = OrderedDict(sorted(self._config.items(), key=key, reverse=reverse))
            return

        self._config = sorted(self._config, key=key, reverse=reverse)

    def keys(self):
        return self._config.keys()

    def __len__(self):
        return len(self._config)

    def __repr__(self):
        return f"<Config raw={self._config} path={self._path_from_root} file={self._file_path}>"

    def __iter__(self):
        return iter(self._config)

    def __contains__(self, item):
        return item in self._config

    def __getitem__(self, item):
        try:
            ret = self._config[item]
        except KeyError:
            self._key_not_found_message_box(item)
            raise
        else:
            if type(ret) in [dict, list, tuple, set]:
                ret = Config(ret, path_from_root=self._path_from_root + [item], file_path=self._file_path)

            return ret


_screen = read_default_yaml(os.path.join(BASE_PATH, 'Screen.yaml'), {
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
})

try:
    MinimumSize = tuple(int(_screen["MinimumSize"][key]) for key in ("width", "height"))
except KeyError:
    MinimumSize = (680, 520)

_font = _screen.get_default("Default Font", Config({}))
_font_size = _font.get_default("Font Size", Config({}))

FontFamily = _font.get_default("family", "Arial")

TinyFont = _font_size.get_default("Tiny", 8)
SmallFont = _font_size.get_default("Small", 10)
NormalFont = _font_size.get_default("Normal", 12)
LargeFont = _font_size.get_default("Large", 14)
HugeFont = _font_size.get_default("Huge", 16)
TitleFont = _font_size.get_default("Title", 20)
