@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

echo ---------------------------------------
echo TESTING JULABO Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d julabo -p %EPICS_KIT_ROOT%\ioc\master\JULABO\iocBoot\iocJULABO-IOC-01 -e %PYTHONDIR%\Scripts -ep julabo-version-1
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING AMINT2L Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d amint2l -p %EPICS_KIT_ROOT%\ioc\master\AMINT2L\iocBoot\iocAMINT2L-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;


echo ---------------------------------------
echo TESTING JULABO Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d julabo -p %EPICS_KIT_ROOT%\ioc\master\JULABO\iocBoot\iocJULABO-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING AMINT2L Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d amint2l -p %EPICS_KIT_ROOT%\ioc\master\AMINT2L\iocBoot\iocAMINT2L-IOC-01
echo ---------------------------------------
echo;


echo ---------------------------------------
echo TESTING INSTRON Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d instron_stress_rig -p %EPICS_KIT_ROOT%\ioc\master\INSTRON\iocBoot\iocINSTRON-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING INSTRON Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d instron_stress_rig -p %EPICS_KIT_ROOT%\ioc\master\INSTRON\iocBoot\iocINSTRON-IOC-01
echo ---------------------------------------
echo;

