@ECHO OFF
REM -*- coding: gbk -*-
REM ������ڵ����

TITLE Build Tool

START /WAIT /B BuildCore

IF %ERRORLEVEL% NEQ 0  (
  TITLE ERROR %ERRORLEVEL%
  ECHO "�ű����쳣��ֹ (%ERRORLEVEL%)"
  TITLE BuildFinish - Error: %ERRORLEVEL%
  GOTO EOF
)
ECHO �����ɹ�! (%ERRORLEVEL%)
TITLE BuildFinish - Successful!

CHOICE /M "���ڿ�ʼ"
IF %ERRORLEVEL% NEQ 1 (
  GOTO EOF
)
CD "../dist/ServerScanner"
START /WAIT /B DebugConsole
EXIT 0
:EOF
TIMEOUT 3 /NOBREAK > NUL
PAUSE
