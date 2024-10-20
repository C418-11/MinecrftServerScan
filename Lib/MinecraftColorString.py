# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.2Dev"

import sys
from dataclasses import dataclass
from typing import Self
from typing import Optional
from typing import TypeVar
from numbers import Integral as Int

ColorName2Code = {
    "black": "§0",
    "dark_blue": "§1",
    "dark_green": "§2",
    "dark_aqua": "§3",
    "dark_red": "§4",
    "dark_purple": "§5",
    "gold": "§6",
    "gray": "§7",
    "dark_gray": "§8",
    "blue": "§9",
    "green": "§a",
    "aqua": "§b",
    "red": "§c",
    "light_purple": "§d",
    "yellow": "§e",
    "white": "§f",
}

CtrlName2Code = {
    "obfuscated": "§k",
    "bold": "§l",
    "strikethrough": "§m",
    "underline": "§n",
    "italic": "§o",

    "reset": "§r",
}

CodeState = {
    **{v: {"StackableWithOtherCodes": False} for v in ColorName2Code.values()},
    **{v: {"StackableWithOtherCodes": True} for v in CtrlName2Code.values()},
    "§r": {"StackableWithOtherCodes": False}
}

Code2ColorName = {v: k for k, v in ColorName2Code.items()}
Code2CtrlName = {v: k for k, v in CtrlName2Code.items()}

Name2Code = {**ColorName2Code, **CtrlName2Code}
Code2Name = {**Code2ColorName, **Code2CtrlName}

ColorCodes = set(ColorName2Code.values())
CtrlCodes = set(CtrlName2Code.values())
Codes = ColorCodes | CtrlCodes

ColorNames = set(ColorName2Code.keys())
CtrlNames = set(CtrlName2Code.keys())
Names = ColorNames | CtrlNames

ColorName2ANSI = {
    "black": "\033[30m",
    "dark_blue": "\033[34m",
    "dark_green": "\033[32m",
    "dark_aqua": "\033[36m",
    "dark_red": "\033[31m",
    "dark_purple": "\033[35m",
    "gold": "\033[33m",
    "gray": "\033[37m",
    "dark_gray": "\033[90m",
    "blue": "\033[94m",
    "green": "\033[92m",
    "aqua": "\033[96m",
    "red": "\033[91m",
    "light_purple": "\033[95m",
    "yellow": "\033[93m",
    "white": "\033[97m",
}

CtrlName2ANSI = {
    "obfuscated": "\033[8m",
    "bold": "\033[1m",
    "strikethrough": "\033[9m",
    "underline": "\033[4m",
    "italic": "\033[3m",

    "reset": "\033[0m",
}

Name2ANSI = {**ColorName2ANSI, **CtrlName2ANSI}

ColorName2RGB = {
    "black": (0, 0, 0),
    "dark_blue": (0, 0, 170),
    "dark_green": (0, 170, 0),
    "dark_aqua": (0, 170, 170),
    "dark_red": (170, 0, 0),
    "dark_purple": (170, 0, 170),
    "gold": (255, 170, 0),
    "gray": (170, 170, 170),
    "dark_gray": (85, 85, 85),
    "blue": (85, 85, 255),
    "green": (85, 255, 85),
    "aqua": (85, 255, 255),
    "red": (255, 85, 85),
    "light_purple": (255, 85, 255),
    "yellow": (255, 255, 85),
    "white": (255, 255, 255),
}

CtrlName2RGB = {
    "reset": (255, 255, 255),

    "obfuscated": None,
    "bold": None,
    "strikethrough": None,
    "underline": None,
    "italic": None,
}

Name2RGB = {**ColorName2RGB, **CtrlName2RGB}
RGB2ColorName = {v: k for k, v in ColorName2RGB.items()}


def hex_to_rgb(hex_str: str) -> tuple[int, ...]:
    if hex_str.startswith("#"):
        hex_str = hex_str[1:]

    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)

    return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: Int, g: Int, b: Int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_ansi(r: Int, g: Int, b: Int) -> str:
    # 计算红、绿、蓝三种颜色通道的强度值所对应的 ANSI 转义码
    return f"\033[38;2;{r};{g};{b}m"


def string_to_code_list(string: str) -> list[list[list[str] | str]]:
    """Convert the string to a list of lists of strings and codes"""

    color_with_str = []
    cache_codes = []
    cache_string = ''
    while string:
        try:
            i = string.index('§')
        except ValueError:
            break
        try:
            code = string[i:i + 2]
        except IndexError:
            break

        if code not in Codes:
            print(f"Unknown code: {code}", file=sys.stderr)
            # 把这个code原样加进去
            cache_string += code
            string = string[i + 1:]
            continue

        tmp_string = string[:i]
        tmp_string.replace(code, '')

        if CodeState[code]["StackableWithOtherCodes"]:
            cache_string += tmp_string
        elif cache_string or cache_codes:
            color_with_str.append([cache_codes.copy(), cache_string + tmp_string])
            cache_codes.clear()
            cache_string = ''

        cache_codes.append(code)

        string = string[i + 2:]

    if string:
        color_with_str.append([cache_codes.copy(), string])

    return color_with_str


I1 = TypeVar("I1", bound=Int)
I2 = TypeVar("I2", bound=Int)
I3 = TypeVar("I3", bound=Int)


def getSimilarRGB(r: I1, g: I2, b: I3) -> tuple[I1, I2, I3]:
    build_in_rgb: list[list[int, int, int]] = list(RGB2ColorName.keys())
    # 在build_in_rgb中查找与r,g,b最接近的颜色并返回那个最接近的颜色
    nearest_rgb = (None, None, None)
    for i, rgb in enumerate(build_in_rgb):
        if nearest_rgb[0] is None:
            nearest_rgb = rgb
            continue

        abs_r = abs(rgb[0] - r)
        abs_g = abs(rgb[1] - g)
        abs_b = abs(rgb[2] - b)

        if abs_r + abs_g + abs_b < abs(nearest_rgb[0] - r) + abs(nearest_rgb[1] - g) + abs(nearest_rgb[2] - b):
            nearest_rgb = rgb

    return nearest_rgb[0], nearest_rgb[1], nearest_rgb[2]


def generate_html_text(special_controls: list[str], color: tuple[Int, Int, Int], text) -> str:
    # 初始化一个空字符串，用来存放生成的HTML文本
    html_text = ""

    # 设置文本颜色
    html_text += f"<span style='color: rgb({color[0]}, {color[1]}, {color[2]});'>"

    # 根据特殊控制列表，应用相应的HTML标签
    if "bold" in special_controls:
        html_text += "<strong>"

    if "italic" in special_controls:
        html_text += "<em>"

    if "underline" in special_controls:
        html_text += "<u>"

    if "strikethrough" in special_controls:
        html_text += "<s>"

    # 添加文本
    html_text += text

    # 关闭HTML标签
    if "strikethrough" in special_controls:
        html_text += "</s>"

    if "underline" in special_controls:
        html_text += "</u>"

    if "italic" in special_controls:
        html_text += "</em>"

    if "bold" in special_controls:
        html_text += "</strong>"

    # 关闭span标签
    html_text += "</span>"

    return html_text


ColorData = dict[str, list[str] | list[int, int, int] | str]


@dataclass
class ColorStringStructure:
    text: str = ''
    color: tuple[int, int, int] = ColorName2RGB["white"]
    ctrls: Optional[list[str]] = None


class ColorString:
    def __init__(self, raw_data: list[ColorStringStructure]):
        self._raw_data: list[ColorStringStructure] = raw_data

    @property
    def raw_data(self) -> list[ColorStringStructure]:
        return self._raw_data.copy()

    @classmethod
    def from_dict(cls, json_dict: dict) -> Self:
        class ParseType:
            Extra = "extra"
            Text = "text"
            Unknown = None

        parse_type = ParseType.Unknown
        if "extra" in json_dict:
            parse_type = ParseType.Extra
        elif "text" in json_dict:
            parse_type = ParseType.Text
        elif "translate" in json_dict:
            parse_type = ParseType.Text
            json_dict["text"] = json_dict["translate"]
        elif type(json_dict) is str:
            parse_type = ParseType.Text
            json_dict = {"text": json_dict}

        def _parse_extra(data: dict) -> list[ColorStringStructure]:
            rets = []
            for item in data["extra"]:
                rets.append(_parse_text(item))

            return rets

        def _parse_text(data: dict) -> ColorStringStructure:
            if type(data) is not dict:
                data = {"text": str(data)}

            string = data["text"]

            ctrls = []
            rgb_color = (255, 255, 255)

            for code in CtrlNames:
                if data.get(code):
                    ctrls.append(code)

            if data.get("color"):
                color: str = data["color"]
                if color not in ColorNames:
                    rgb_color = hex_to_rgb(color)
                else:
                    rgb_color = Name2RGB[color]

            return ColorStringStructure(text=string, color=rgb_color, ctrls=ctrls)

        if parse_type == ParseType.Extra:
            result = _parse_extra(json_dict)

        elif parse_type == ParseType.Text:
            result = [_parse_text(json_dict)]
        else:
            print(json_dict)
            raise ValueError("Unknown parse type")

        return cls(result)

    @classmethod
    def from_string(cls, string: str) -> Self:
        data = []
        for code_list, text in string_to_code_list(string):
            ctrls = []
            color_rgb = (255, 255, 255)
            for code in code_list:
                code_name = Code2Name[code]
                if code in CtrlCodes:
                    ctrls.append(code_name)
                    continue

                color_rgb = ColorName2RGB[code_name]

            data.append(ColorStringStructure(text=text, color=color_rgb, ctrls=ctrls))
        return cls(data)

    def to_ansi(self) -> str:
        string = ''
        for item in self._raw_data:
            ansi_cache = []
            for ctrl in item.ctrls:
                ansi_cache.append(Name2ANSI[ctrl])
            ansi_cache.append(rgb_to_ansi(*item.color))
            string += ''.join(ansi_cache)
            string += item.text

        return string

    def to_string(self) -> str:
        string = ''
        for item in self._raw_data:
            code_cache = []
            for ctrl in item.ctrls:
                code_cache.append(CtrlName2Code[ctrl])

            code_cache.insert(0, ColorName2Code[RGB2ColorName[getSimilarRGB(*item.color)]])
            string += ''.join(code_cache)
            string += item.text

        return string

    def to_html(self) -> str:
        html_text = ""
        for item in self._raw_data:
            html_text += generate_html_text(item.ctrls, item.color, item.text)
        return html_text

    def to_dict(self) -> dict:
        ret_dict = {"text": '', "extra": []}

        for item in self._raw_data:
            this_dict = {}
            for ctrl in item.ctrls:
                this_dict[ctrl] = True

            if item.color in RGB2ColorName:
                this_dict["color"] = RGB2ColorName[item.color]
            else:
                this_dict["color"] = rgb_to_hex(*item.color)
            this_dict["text"] = item.text

            ret_dict["extra"].append(this_dict)

        return ret_dict

    def to_json(self):
        import json
        return json.dumps(self.to_dict())

    def __repr__(self):
        return f"<ColorString: {self._raw_data}>"

    def __str__(self):
        return self.to_string()


__all__ = (
    "ColorName2Code",
    "CtrlName2Code",
    "Code2ColorName",
    "Code2CtrlName",
    "Name2Code",
    "Code2Name",

    "ColorCodes",
    "CtrlCodes",
    "ColorNames",
    "CtrlNames",
    "Codes",
    "Names",

    "ColorName2ANSI",
    "CtrlName2ANSI",
    "Name2ANSI",

    "ColorName2RGB",
    "CtrlName2RGB",
    "Name2RGB",
    "RGB2ColorName",

    "CodeState",

    "getSimilarRGB",

    "ColorStringStructure",
    "ColorString",
)
