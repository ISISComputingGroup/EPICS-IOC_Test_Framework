@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

echo ---------------------------------------
echo TESTING READASCII
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d readascii -p %EPICS_KIT_ROOT%\support\ReadASCII\master\iocBoot\iocReadASCIITest
echo ---------------------------------------
echo;
