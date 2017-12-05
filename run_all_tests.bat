@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

echo ---------------------------------------
echo TESTING GEMORC Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d gemorc -p %EPICS_KIT_ROOT%\ioc\master\GEMORC\iocBoot\iocGEMORC-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;
REM 
REM echo ---------------------------------------
REM echo TESTING GEMORC Rec Sim
REM call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d gemorc -p %EPICS_KIT_ROOT%\ioc\master\GEMORC\iocBoot\iocGEMORC-IOC-01
REM echo ---------------------------------------
REM echo;
