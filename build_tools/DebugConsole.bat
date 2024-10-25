@ECHO OFF
REM -*- coding: gbk -*-
REM 简单的调试脚本(单纯是为了给EXE提供一个stdout)

TITLE 调试控制台
ECHO 已启用调试控制台
START /WAIT /B  ./ServerScanner.exe

TIMEOUT 1 /NOBREAK > NUL
ECHO 键入任意键关闭窗口
PAUSE > NUL
EXIT 0
