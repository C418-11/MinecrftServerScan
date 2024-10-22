@ECHO OFF
REM -*- coding: utf-8 -*-

D:
CD D:\$.MSS
ECHO Removing D:/$.MSS/C
RMDIR /S /Q "./C"
ECHO Removing D:/$.MSS/T
RMDIR /S /Q "./T"
EXIT