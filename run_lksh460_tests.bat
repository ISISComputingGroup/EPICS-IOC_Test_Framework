@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

echo ---------------------------------------
echo TESTING LKSH460 Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d lakeshore460 -p %EPICS_KIT_ROOT%\ioc\master\LKSH460\iocBoot\iocLKSH460-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING LKSH460 Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d lakeshore460 -p %EPICS_KIT_ROOT%\ioc\master\LKSH460\iocBoot\iocLKSH460-IOC-01

echo ---------------------------------------
echo;
