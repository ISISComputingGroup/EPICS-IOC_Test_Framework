@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

set "PYTHONUNBUFFERED=1"

call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py"
