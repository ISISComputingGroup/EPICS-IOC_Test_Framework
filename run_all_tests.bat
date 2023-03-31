@echo off
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
if "%COMPUTERNAME%" == "NDHSPARE70" (
    set "DEBUGGERCMD=C:\Users\ibexbuilder\Downloads\DrMemory-Windows-2.5.19327\DrMemory-Windows-2.5.19327\bin64\drmemory.exe"
    set "DEBUGGERARGS=-report_max -1 -no_check_uninitialized -no_follow_children --"
)

REM Command line arguments always passed to the test script
SET ARGS=-rc
REM we use the python3 executable rather than python as this allows us to
REM configure the applicatrion verifier for python3.exe and we don't get
REM a lot of logs every time tests spawn python.exe for e.g. emulators
if not "%DEBUGGERCMD%" == "" (
    "%DEBUGGERCMD%" %DEBUGGERARGS% "c:\instrument\Apps\python3\python3.exe" -u "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" %ARGS% %*
) else (
    "c:\Instrument\Apps\Python3\Python3.exe" -u "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" %ARGS% %* 
)
IF %ERRORLEVEL% NEQ 0 EXIT /b %errorlevel%
