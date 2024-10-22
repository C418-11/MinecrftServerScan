@ECHO OFF
REM -*- coding: utf-8 -*-
REM 构建入口

TITLE BuildTool - Prepare

IF EXIST "D:\$.MSS\CleanBuild.bat" (
  ECHO Cleaning last build...
  START "Cleaning last build..." /WAIT /B "D:\$.MSS\CleanBuild.bat"
  IF %ERRORLEVEL% NEQ 0 (
    ECHO "Clean last build failed... (%ERRORLEVEL%)"
    EXIT -2
  )
)

IF NOT EXIST .log (
  MKDIR .log
)

IF EXIST Build/pyd (
  ECHO Cleaning old pyd...
  RMDIR /S "Build/pyd"
)
IF EXIST Build/pyd (
  ECHO Old pyd must be delete
  EXIT -1
)

TITLE BuildTool - Build

ECHO Building pyd... (logging with ".log\latest-pyd.txt")
START /B /WAIT BuildPyd > ".log\latest-pyd.txt"
IF %ERRORLEVEL% NEQ 0 (
  ECHO Somthing wrong during build pyd...
  EXIT 1
)
COPY /V CleanBuild.bat "D:\$.MSS"

ECHO Building exe...
START /B /WAIT BuildExe
IF %ERRORLEVEL% NEQ 0 (
  ECHO Something wrong during build exe...
  EXIT 2
)

TITLE BuildTool - CopyFiles

ECHO Copying files...
START /B /WAIT CopyFiles
IF %ERRORLEVEL% NEQ 0 (
  ECHO Something wrong during copy files...
  EXIT 3
)

TITLE BuildFinish
EXIT 0
