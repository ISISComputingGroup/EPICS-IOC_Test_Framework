@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

echo ---------------------------------------
echo TESTING RIKEN PORT CHANGEOVER
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -tm rikenportchangeover
echo ---------------------------------------
echo;
