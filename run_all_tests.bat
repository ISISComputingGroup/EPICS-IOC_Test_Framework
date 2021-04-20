@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

set "PYTHONUNBUFFERED=1"

REM Command line arguments always passed to the test script
SET ARGS=-rc

call %PYTHON3% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" %ARGS% %* 
IF %ERRORLEVEL% NEQ 0 EXIT /b %errorlevel%
