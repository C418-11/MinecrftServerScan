# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "MSS-0.0.3Bata"

import importlib
import os.path
import re
import sys
import traceback

import colorama

from Lib.Configs import BASE_PATH
from Lib.Configs import read_default_yaml
from Lib.StdColor import ColorWrite

DefaultFeatures = read_default_yaml(
    os.path.join(BASE_PATH, "DefaultFeatures.yaml"),
    {
        "1|WindowTop": True,  # 这里的 '|' 是为了读取后进行排序
        "2|Opacity": True,
        "3|ScanServer": True,
        "4|ScanSettings": False,
    }
)

DefaultFeatures.sort()

_yellow_write = ColorWrite(sys.stdout, colorama.Fore.LIGHTYELLOW_EX)
_blue_write = ColorWrite(sys.stdout, colorama.Fore.LIGHTBLUE_EX)
_red_write = ColorWrite(sys.stdout, colorama.Fore.LIGHTRED_EX)


def _load(name: str, import_path: str):
    try:
        module = importlib.import_module(f"{import_path}.{name}")
        print("Feature loaded successfully:", name, file=_yellow_write)

        _show_details(module)
        return module
    except ImportError as err:
        traceback.print_exception(err)
        c = re.compile(r"No\smodule\snamed\s'([^']+)'")
        err_module = c.findall(str(err))

        if (not err_module) or len(err_module) != 1:
            print("Unable to load Feature:", name, " reason:", err, file=_red_write)
            return None

        err_module = err_module[0]

        if err_module == import_path:
            print("Feature not found:", f"{import_path}.{name}", file=_blue_write)
            return None

        if err_module == f"{import_path}.{name}":
            print("Feature not found:", f"{import_path}.{name}", file=_blue_write)
            return None

        print(f"Unable to load Feature '{name}', dependencies may not be installed: '{err_module}'", file=_red_write)
        return None
    except Exception as err:
        traceback.print_exception(err)
        print("Unable to load Feature:", name, " reason:", err, file=_red_write)
        return None


def _get_details(module):
    detail_dict = {}

    for attr in ("__author__", "__description__", "__version__"):
        value = getattr(module, attr, None)

        if value is not None:
            detail_dict[attr] = value

    return detail_dict


def _show_details(module):
    details = _get_details(module)

    if not details:
        print("  No details available", file=_yellow_write)
        return

    key_map = {
        "__author__": "Auther",
        "__description__": "Desc",
        "__version__": "Ver"
    }

    for attr, value in details.items():
        print(f"  {key_map[attr]}: {value}", file=_yellow_write)


def load_default_features():
    lib_path = os.path.join(os.path.dirname(__file__), "DefaultFeatures")
    sys.path.append(lib_path)

    loaded_features = {}
    for feature in DefaultFeatures:
        if not bool(DefaultFeatures[feature]):
            print("Feature disabled:", feature, file=_blue_write)
            loaded_features[feature] = None
            continue
        if '|' in feature:
            feature = feature.split('|')[1]
        loaded_features[feature] = _load(feature, "DefaultFeatures")

    return loaded_features


OtherFeatures = read_default_yaml(
    os.path.join(BASE_PATH, "OtherFeatures.yaml"),
    {
        "YourFeatureName": "Is Enabled (true | false)",
        "HelloWorld": False
    }
)

OtherFeatures.sort()


def load_other_features():
    lib_path = os.path.join(os.path.dirname(__file__), "OtherFeatures")
    sys.path.append(lib_path)

    loaded_features = {}
    for feature in OtherFeatures:
        if feature == "YourFeatureName":
            print("YourFeatureName is a reserved keyword, please change it to another name.", file=_red_write)
            continue

        if not OtherFeatures[feature]:
            print("Feature disabled:", feature, file=_blue_write)
            loaded_features[feature] = None
            continue
        if '|' in feature:
            feature = feature.split('|')[1]

        loaded_features[feature] = _load(feature, "Features")

    return loaded_features


__all__ = ("DefaultFeatures", "load_default_features", "OtherFeatures", "load_other_features")
