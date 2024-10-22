@ECHO OFF
REM -*- coding: utf-8 -*-
REM 循环内层的语句块

IF /I %3 NEQ "<DIR>" (
  ECHO Copying '%1\%~nx4' to '%2\%~nx4'...
  COPY "%1\%~nx4" "%2\%~nx4"
  IF %ERRORLEVEL% NEQ 0 (
    EXIT %ERRORLEVEL%
  )
)

IF /I %3 EQU "<DIR>" (
  MKDIR %2\%~n4
  IF %ERRORLEVEL% NEQ 0 (
    IF %ERRORLEVEL% NEQ 1 (
      ECHO Failed build path '%2\%~nx4'...
      EXIT %ERRORLEVEL%
    )
  )
  START /WAIT /B CMD /C "CALL .\RecursiveCopy\Copy %1\%~n4 %2\%~n4"
  IF %ERRORLEVEL% NEQ 0 (
    EXIT %ERRORLEVEL%
  )
)
