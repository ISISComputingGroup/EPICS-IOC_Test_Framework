@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

echo ---------------------------------------
echo TESTING AMINT2L Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm amint2l -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING AMINT2L Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm amint2l
echo ---------------------------------------
echo;


