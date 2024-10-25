@ECHO OFF
REM -*- coding: gbk -*-
REM 构建入口的外壳

TITLE Build Tool

START /WAIT /B BuildCore

IF %ERRORLEVEL% NEQ 0  (
  TITLE ERROR %ERRORLEVEL%
  ECHO "脚本因异常终止 (%ERRORLEVEL%)"
  TITLE BuildFinish - Error: %ERRORLEVEL%
  GOTO EOF
)
ECHO 构建成功! (%ERRORLEVEL%)
TITLE BuildFinish - Successful!

CHOICE /M "现在开始"
IF %ERRORLEVEL% NEQ 1 (
  GOTO EOF
)
CD "../dist/ServerScanner"
START /WAIT /B DebugConsole
EXIT 0
:EOF
TIMEOUT 3 /NOBREAK > NUL
PAUSE
