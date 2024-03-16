# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import sys
import warnings

if not (3, 10) < sys.version_info < (3, 11):
    warnings.warn(
        "Python 3.10.x is not supported by this package. "
        "It may not work properly.",
        DeprecationWarning,
    )

__all__ = ("Events", "Scanner")
