@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

set "PYTHONUNBUFFERED=1"

REM on NDHSPARE70 launch under Dr. Memory (to attempt to diagnose a memory fault; see https://github.com/ISISComputingGroup/IBEX/issues/7643)
if "%COMPUTERNAME%" == "NDHSPARE70" (
    set "DEBUGGERCMD=C:\Users\ibexbuilder\Downloads\DrMemory-Windows-2.5.19327\DrMemory-Windows-2.5.19327\bin64\drmemory.exe -report_max -1 -no_check_uninitialized -no_follow_children --"
) else (
    set "DEBUGGERCMD="
)

REM Command line arguments always passed to the test script
SET ARGS=-rc
call %DEBUGGERCMD% %PYTHON3% -u "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" %ARGS% %* 
IF %ERRORLEVEL% NEQ 0 EXIT /b %errorlevel%
