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
echo TESTING JULABO Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d julabo -p %EPICS_KIT_ROOT%\ioc\master\JULABO\iocBoot\iocJULABO-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING TPG26X Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d tpg26x -p %EPICS_KIT_ROOT%\ioc\master\TPG26x\iocBoot\iocTPG26x-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING TPG26X Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d tpg26x -p %EPICS_KIT_ROOT%\ioc\master\TPG26x\iocBoot\iocTPG26x-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING AMINT2L Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d amint2l -p %EPICS_KIT_ROOT%\ioc\master\AMINT2L\iocBoot\iocAMINT2L-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
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

echo ---------------------------------------
echo TESTING AG33220A Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d ag33220a -p %EPICS_KIT_ROOT%\ioc\master\AG33220A\iocBoot\iocAG33220A-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING FERMI CHOPPER Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d fermichopper -p %EPICS_KIT_ROOT%\ioc\master\FERMCHOP\iocBoot\iocFERMCHOP-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING XYARMBEAMSTOP Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d xyarmbeamstop -p %EPICS_KIT_ROOT%\ioc\master\GALIL\iocBoot\iocGALIL-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING FERMI CHOPPER Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d fermichopper -p %EPICS_KIT_ROOT%\ioc\master\FERMCHOP\iocBoot\iocFERMCHOP-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING KEPCO Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d kepco -p %EPICS_KIT_ROOT%\ioc\master\KEPCO\iocBoot\iocKEPCO-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING KEPCO Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d kepco -p %EPICS_KIT_ROOT%\ioc\master\KEPCO\iocBoot\iocKEPCO-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING TDK_LAMBDA_GENESYS Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d tdk_lambda_genesys -p %EPICS_KIT_ROOT%\ioc\master\TDK_LAMBDA_GENESYS\iocBoot\iocGENESYS-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING TDK_LAMBDA_GENESYS Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d tdk_lambda_genesys -p %EPICS_KIT_ROOT%\ioc\master\TDK_LAMBDA_GENESYS\iocBoot\iocGENESYS-IOC-01
echo ---------------------------------------
echo;

REM SAMPOS has no dev sim as it is an LvDCOM IOC

echo ---------------------------------------
echo TESTING SAMPOS Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d sampos -p %EPICS_KIT_ROOT%\ioc\master\SAMPOS\iocBoot\iocSAMPOS
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING RKNPS Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d rknps -p %EPICS_KIT_ROOT%\ioc\master\RKNPS\iocBoot\iocRKNPS-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING RKNPS Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d rknps -p %EPICS_KIT_ROOT%\ioc\master\RKNPS\iocBoot\iocRKNPS-IOC-01
echo ---------------------------------------
echo;
echo ---------------------------------------
echo TESTING CYBAMAN Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d cybaman -p %EPICS_KIT_ROOT%\ioc\master\CYBAMAN\iocBoot\iocCYBAMAN-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING CYBAMAN Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d cybaman -p %EPICS_KIT_ROOT%\ioc\master\CYBAMAN\iocBoot\iocCYBAMAN-IOC-01
echo ---------------------------------------
echo;

REM EGXCOLIM has no dev sim as it is an LvDCOM IOC

echo ---------------------------------------
echo TESTING EGXCOLIM Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d egxcolim -p %EPICS_KIT_ROOT%\ioc\master\EGXCOLIM\iocBoot\iocEGXCOLIM-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING IEG Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d ieg -p %EPICS_KIT_ROOT%\ioc\master\IEG\iocBoot\iocIEG-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------

echo ---------------------------------------
echo TESTING IEG Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d ieg -p %EPICS_KIT_ROOT%\ioc\master\IEG\iocBoot\iocIEG-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING HLG Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d hlg -p %EPICS_KIT_ROOT%\ioc\master\HLG\iocBoot\iocHLG-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING HLG Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d hlg -p %EPICS_KIT_ROOT%\ioc\master\HLG\iocBoot\iocHLG-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING EUROTHRM Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d eurotherm -p %EPICS_KIT_ROOT%\ioc\master\EUROTHRM\iocBoot\iocEUROTHRM-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING OSCILLATING COLLIMATOR Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d oscillating_collimator -p %EPICS_KIT_ROOT%\ioc\master\GALIL\iocBoot\iocGALIL-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING FERMI CHOPPER LIFTER Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d fermi_chopper_lifter -p %EPICS_KIT_ROOT%\ioc\master\GALIL\iocBoot\iocGALIL-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING MK3Chopper Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d mk3chopper -p %EPICS_KIT_ROOT%\ioc\master\MK3CHOPR\iocBoot\iocMK3CHOPR-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING MK3Chopper Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d mk3chopper -p %EPICS_KIT_ROOT%\ioc\master\MK3CHOPR\iocBoot\iocMK3CHOPR-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING GEMORC Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d gemorc -p %EPICS_KIT_ROOT%\ioc\master\GEMORC\iocBoot\iocGEMORC-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING GEMORC Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d gemorc -p %EPICS_KIT_ROOT%\ioc\master\GEMORC\iocBoot\iocGEMORC-IOC-01
echo ---------------------------------------
echo;
