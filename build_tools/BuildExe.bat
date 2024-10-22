@ECHO OFF
REM -*- coding: utf-8 -*-
REM 构建EXE

CALL BuildConfig

CD ..
IF %ERRORLEVEL% NEQ 0 (
  ECHO Dir Not Found.
  EXIT %ERRORLEVEL%
)
IF NOT EXIST "%CONFIG_PYINSTALLER%" (
  ECHO Pyinstaller not found.
  EXIT %ERRORLEVEL%
)

START /B /WAIT %CONFIG_PYINSTALLER% -D main.py -n ServerScan -i "icon16px.png" --clean -y --hide-console hide-early
IF %ERRORLEVEL% NEQ 0 (
  ECHO "Error. (%ERRORLEVEL%)"
  EXIT %ERRORLEVEL%
)
EXIT 0
