@ECHO OFF
REM -*- coding: gbk -*-
REM �򵥵ĵ��Խű�(������Ϊ�˸�EXE�ṩһ��stdout)

TITLE ���Կ���̨
ECHO �����õ��Կ���̨
START /WAIT /B  ./ServerScanner.exe

TIMEOUT 1 /NOBREAK > NUL
ECHO ����������رմ���
PAUSE > NUL
EXIT 0
