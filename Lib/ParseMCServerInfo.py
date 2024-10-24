# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import base64
import io
from abc import ABC

from Lib.MinecraftColorString import ColorString


class ForInRepr(ABC):
    def __repr__(self):
        attrs = []
        for attr in dir(self):
            if attr.startswith("_"):
                continue

            value = getattr(self, attr)
            value_str = repr(value).replace('\n', "\n    ")

            attrs.append(f"   {attr}={value_str}")

        joined_attr = ", \n".join(attrs)
        return f"<{type(self).__name__} (\n{joined_attr}\n)>"


class Players(ForInRepr):
    class Sample(ForInRepr):
        def __init__(self, raw_data: dict):
            self._raw_data = raw_data

        @property
        def id(self) -> str:
            return self._raw_data["id"]

        @property
        def name(self) -> ColorString:
            return ColorString.from_string(self._raw_data["name"])

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def max(self) -> int:
        return self._raw_data["max"]

    @property
    def online(self) -> int:
        return self._raw_data["online"]

    @property
    def sample(self) -> list[Sample] | None:
        data = self._raw_data.get("sample")
        if data is None:
            return None
        return [self.Sample(x) for x in data]


class ForgeData(ForInRepr):
    class Channel(ForInRepr):
        def __init__(self, raw_data: dict):
            self._raw_data = raw_data

        @property
        def res(self) -> str:
            return self._raw_data["res"]

        @property
        def version(self) -> str:
            return self._raw_data["version"]

        @property
        def required(self) -> bool:
            return self._raw_data["required"]

    class Mod(ForInRepr):
        def __init__(self, raw_data: dict):
            self._raw_data = raw_data

        @property
        def modId(self) -> str:
            return self._raw_data["modId"]

        # noinspection SpellCheckingInspection
        @property
        def modmarker(self) -> str:
            return self._raw_data["modmarker"]

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
    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def name(self) -> str:
        return self._raw_data["name"]

    @property
    def protocol(self) -> int:
        return self._raw_data["protocol"]


class Favicon:
    def __init__(self, raw_data: str):
        self._raw_data = raw_data

    @property
    def raw(self) -> str:
        return self._raw_data

    def to_bytes(self) -> bytes:
        return base64.b64decode(self._raw_data.split(',')[1])

    def to_file(self, path: str):
        with open(path, "wb") as f:
            f.write(self.to_bytes())

    def to_image(self):
        from PIL import Image
        return Image.open(io.BytesIO(self.to_bytes()))

    def __repr__(self):
        return f"<Favicon: {self._raw_data}>"

    def __str__(self):
        return self._raw_data


class ServerInfo(ForInRepr):
    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def raw_data(self):
        return self._raw_data

    @property
    def description(self) -> ColorString:
        return ColorString.from_obj(self._raw_data["description"])

    @property
    def players(self) -> Players:
        return Players(self._raw_data["players"])

    @property
    def version(self) -> Version:
        return Version(self._raw_data["version"])

    @property
    def forgeData(self) -> ForgeData | None:
        data = self._raw_data.get("forgeData")
        if data is None:
            return None
        return ForgeData(self._raw_data["forgeData"])

    @property
    def favicon(self) -> Favicon | None:
        data = self._raw_data.get("favicon")
        if data is None:
            return None
        return Favicon(data)
