@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

echo ---------------------------------------
echo TESTING EUROTHRM Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -r -d eurotherm -p %EPICS_KIT_ROOT%\ioc\master\EUROTHRM\iocBoot\iocEUROTHRM-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING EUROTHRM Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d eurotherm -p %EPICS_KIT_ROOT%\ioc\master\EUROTHRM\iocBoot\iocEUROTHRM-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;
