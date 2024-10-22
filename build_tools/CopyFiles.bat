@ECHO OFF
REM -*- coding: utf-8 -*-
REM 将构建好的必要文件复制到输出目录

IF NOT EXIST "..\dist\ServerScan" (
  ECHO Output dir not found.
  EXIT 9009
)
COPY /V "DebugConsole.bat" "..\dist\ServerScan"
IF %ERRORLEVEL% NEQ 0 (
  ECHO Warning: Failed copy debug script...
)

TITLE Copy pyd files

START /WAIT /B CMD /C "CALL RecursiveCopy\Copy Build\pyd ..\dist\ServerScan\_internal"
IF %ERRORLEVEL% NEQ 0 (
  ECHO "Error during copy pyd files... (%ERRORLEVEL%)"
  EXIT %ERRORLEVEL%
)

TITLE Copy Textures

MKDIR "..\dist\ServerScan\Textures"
IF %ERRORLEVEL% NEQ 0 (
  IF %ERRORLEVEL% NEQ 1 (
    ECHO Failed build path '..\dist\ServerScan\Textures'...
    EXIT %ERRORLEVEL%
  )
)
START /WAIT /B CMD /C "CALL RecursiveCopy\Copy ..\Textures ..\dist\ServerScan\Textures"
IF %ERRORLEVEL% NEQ 0 (
  ECHO "Error during copy textures... (%ERRORLEVEL%)"
  EXIT %ERRORLEVEL%
)
EXIT 0
