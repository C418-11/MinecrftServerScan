@ECHO OFF
REM -*- coding: utf-8 -*-
REM 主循环

IF NOT EXIST %1 (
  ECHO Source dir '%1' not found...
  EXIT 9009
)
IF NOT EXIST %2 (
  ECHO Target dir '%2' not found...
  EXIT 9009
)

FOR /F "skip=7 tokens=3,4" %%I IN ('dir %1') DO (
  IF NOT EXIST %1\%%~nxJ (
    GOTO RecursiveCopyEOF
  )
  START /WAIT /B CMD /C "CALL .\RecursiveCopy\BaseBlock %1 %2 "%%I" %%J"
  IF %ERRORLEVEL% NEQ 0 (
    EXIT %ERRORLEVEL%
  )
)
:RecursiveCopyEOF
EXIT 0