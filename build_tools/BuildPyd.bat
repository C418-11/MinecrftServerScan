@ECHO OFF
REM -*- coding: utf-8 -*-
REM 将源码编译为不可读的pyd

CALL BuildConfig

IF NOT EXIST %CONFIG_PYTHON% (
  ECHO "Python Not Found. (projectRoot/venv312/Scripts/)"
  EXIT 9009
)
ECHO 1|START /WAIT /B %CONFIG_PYTHON% setup.py

IF %ERRORLEVEL% NEQ 0 (
  ECHO "Error. (%ERRORLEVEL%)"
  EXIT %ERRORLEVEL%
)
EXIT 0
