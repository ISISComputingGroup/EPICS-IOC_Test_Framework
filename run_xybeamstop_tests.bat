@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

echo ---------------------------------------
echo TESTING XYARMBEAMSTOP Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d xyarmbeamstop -p %EPICS_KIT_ROOT%\ioc\master\GALIL\iocBoot\iocGALIL-IOC-01
echo ---------------------------------------
echo;
