@echo off
setlocal enabledelayedexpansion

REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

set "PYTHONUNBUFFERED=1"

REM use cdb as jenkins is non-interactive
for /D %%I in ( "C:\Program Files (x86)\Windows Kits\*" ) do (
    if exist "%%I\Debuggers\x64\cdb.exe" SET "WINDBG=%%I\Debuggers\x64\cdb.exe"
)

if not "%yyyWINDBG%" == "" (
    set "DEBUGGERCMD=%WINDBG%"
    set "DEBUGGERARGS=-g -xd av -xd ch -xd sov"
) else (
    set "DEBUGGERCMD="
    set "DEBUGGERARGS="
)
REM on NDHSPARE70 launch under Dr. Memory (to attempt to diagnose a memory fault; see https://github.com/ISISComputingGroup/IBEX/issues/7643)
if "%COMPUTERNAME%" == "yyyNDHSPARE70" (
    set "DEBUGGERCMD=C:\Users\ibexbuilder\Downloads\DrMemory-Windows-2.5.19327\DrMemory-Windows-2.5.19327\bin64\drmemory.exe"
    set "DEBUGGERARGS=-report_max -1 -no_check_uninitialized -no_follow_children --"
)

REM Command line arguments always passed to the test script
set "ARGS="
REM only pass -rc if no other args, otherwise if we are running only one test
REM it tells us about all the tests we missed running 
if "%*" == "" SET "ARGS=%ARGS% -rc"
REM we use the python3 executable rather than python as this allows us to
REM configure the applicatrion verifier for python3.exe and we don't get
REM a lot of logs every time tests spawn python.exe for e.g. emulators
:loop
if not "%DEBUGGERCMD%" == "" (
    "%DEBUGGERCMD%" %DEBUGGERARGS% "c:\instrument\Apps\python3\python3.exe" -u "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" %ARGS% %*
) else (
    "%PYTHON3%" -u "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" %ARGS% %* 
)
set errcode=!ERRORLEVEL!
IF %errcode% NEQ 0 (
    @echo ERROR: tests exited with status %errcode%
    EXIT /b %errcode%
)
REM if we wish to continually run tests until failure uncomment this
REM goto loop
