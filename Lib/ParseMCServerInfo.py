# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import base64
import io
from abc import ABC
from Lib.MinecraftColorString import ColorString

from PIL import Image


class ForInRepr(ABC):
    def __repr__(self):
        attrs = []
        for attr in dir(self):
            if attr.startswith("_"):
                continue

            value = getattr(self, attr)
            value_str = repr(value).replace('\n', "\n    ")

            attrs.append(f"   {attr}={value_str}")

        return f"<{type(self).__name__} (\n{", \n".join(attrs)}\n)>"


class Players(ForInRepr):
    class Sample(ForInRepr):
        def __init__(self, raw_dict: dict):
            self._raw_dict = raw_dict

        @property
        def id(self) -> str:
            return self._raw_dict["id"]

        @property
        def name(self) -> ColorString:
            return ColorString.from_string(self._raw_dict["name"])

    def __init__(self, raw_dict: dict):
        self._raw_dict = raw_dict

    @property
    def max(self) -> int:
        return self._raw_dict["max"]

    @property
    def online(self) -> int:
        return self._raw_dict["online"]

    @property
    def sample(self) -> list[Sample] | None:
        data = self._raw_dict.get("sample")
        if data is None:
            return None
        return [self.Sample(x) for x in data]


class ForgeData(ForInRepr):
    class Channel(ForInRepr):
        def __init__(self, raw_dict: dict):
            self._raw_dict = raw_dict

        @property
        def res(self) -> str:
            return self._raw_dict["res"]

        @property
        def version(self) -> str:
            return self._raw_dict["version"]

        @property
        def required(self) -> bool:
            return self._raw_dict["required"]

    class Mod(ForInRepr):
        def __init__(self, raw_dict: dict):
            self._raw_dict = raw_dict

        @property
        def modId(self) -> str:
            return self._raw_dict["modId"]

        # noinspection SpellCheckingInspection
        @property
        def modmarker(self) -> str:
            return self._raw_dict["modmarker"]

    def __init__(self, raw_dict: dict):
        self._raw_dict = raw_dict

    @property
    def channels(self) -> list[Channel]:
        return [self.Channel(x) for x in self._raw_dict["channels"]]

    @property
    def mods(self) -> list[Mod]:
        return [self.Mod(x) for x in self._raw_dict["mods"]]

    @property
    def fmlNetworkVersion(self) -> int:
        return self._raw_dict["fmlNetworkVersion"]

    @property
    def truncated(self) -> bool:
        return self._raw_dict["truncated"]


class Version(ForInRepr):
    def __init__(self, raw_dict: dict):
        self._raw_dict = raw_dict

    @property
    def name(self) -> str:
        return self._raw_dict["name"]

    @property
    def protocol(self) -> int:
        return self._raw_dict["protocol"]


class Favicon:
    def __init__(self, raw_string: str):
        self._raw_string = raw_string

    @property
    def raw(self) -> str:
        return self._raw_string

    def to_bytes(self) -> bytes:
        return base64.b64decode(self._raw_string.split(',')[1])

    def to_file(self, path: str):
        with open(path, "wb") as f:
            f.write(self.to_bytes())

    def to_image(self) -> Image.Image:
        return Image.open(io.BytesIO(self.to_bytes()))

    def __repr__(self):
        return f"<Favicon: {self._raw_string}>"

    def __str__(self):
        return self._raw_string


class ServerInfo(ForInRepr):
    def __init__(self, raw_dict: dict):
        self._raw_dict = raw_dict

    @property
    def description(self) -> ColorString:
        return ColorString.from_dict(self._raw_dict["description"])

    @property
    def players(self) -> Players:
        return Players(self._raw_dict["players"])

    @property
    def version(self) -> Version:
        return Version(self._raw_dict["version"])

    @property
    def forgeData(self) -> ForgeData | None:
        data = self._raw_dict.get("forgeData")
        if data is None:
            return None
        return ForgeData(self._raw_dict["forgeData"])

    @property
    def favicon(self) -> Favicon | None:
        data = self._raw_dict.get("favicon")
        if data is None:
            return None
        return Favicon(data)
