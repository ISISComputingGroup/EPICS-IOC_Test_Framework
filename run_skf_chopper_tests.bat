@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

echo ---------------------------------------
echo TESTING SKF MB350 Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d skf_mb350_chopper -p %EPICS_KIT_ROOT%\ioc\master\SKFMB350\iocBoot\iocSKFMB350-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING SKF MB350 Rec Sim
REM call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d skf_mb350_chopper -p %EPICS_KIT_ROOT%\ioc\master\SKFMB350\iocBoot\iocSKFMB350-IOC-01
echo ---------------------------------------
echo;
