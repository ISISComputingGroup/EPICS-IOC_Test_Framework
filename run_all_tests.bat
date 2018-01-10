@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

echo ---------------------------------------
echo TESTING JULABO Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm julabo -e %PYTHONDIR%\Scripts -ep julabo-version-1
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING JULABO Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm julabo
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING TPG26X Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm tpg26x -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING TPG26X Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm tpg26x
echo ---------------------------------------
echo;
 
echo ---------------------------------------
echo TESTING AMINT2L Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm amint2l -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING AMINT2L Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm amint2l
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING INSTRON Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm instron_stress_rig -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING INSTRON Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm instron_stress_rig
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING AG33220A Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -tm ag33220a -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo;

rem echo ---------------------------------------
rem echo TESTING FERMI CHOPPER Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d fermichopper -p %EPICS_KIT_ROOT%\ioc\master\FERMCHOP\iocBoot\iocFERMCHOP-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING XYARMBEAMSTOP Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d xyarmbeamstop -p %EPICS_KIT_ROOT%\ioc\master\GALIL\iocBoot\iocGALIL-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING FERMI CHOPPER Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d fermichopper -p %EPICS_KIT_ROOT%\ioc\master\FERMCHOP\iocBoot\iocFERMCHOP-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING KEPCO Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d kepco -p %EPICS_KIT_ROOT%\ioc\master\KEPCO\iocBoot\iocKEPCO-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING KEPCO Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d kepco -p %EPICS_KIT_ROOT%\ioc\master\KEPCO\iocBoot\iocKEPCO-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING TDK_LAMBDA_GENESYS Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d tdk_lambda_genesys -p %EPICS_KIT_ROOT%\ioc\master\TDK_LAMBDA_GENESYS\iocBoot\iocGENESYS-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING TDK_LAMBDA_GENESYS Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d tdk_lambda_genesys -p %EPICS_KIT_ROOT%\ioc\master\TDK_LAMBDA_GENESYS\iocBoot\iocGENESYS-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem REM SAMPOS has no dev sim as it is an LvDCOM IOC
rem 
rem echo ---------------------------------------
rem echo TESTING SAMPOS Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d sampos -p %EPICS_KIT_ROOT%\ioc\master\SAMPOS\iocBoot\iocSAMPOS
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING RKNPS Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d rknps -p %EPICS_KIT_ROOT%\ioc\master\RKNPS\iocBoot\iocRKNPS-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING RKNPS Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d rknps -p %EPICS_KIT_ROOT%\ioc\master\RKNPS\iocBoot\iocRKNPS-IOC-01
rem echo ---------------------------------------
rem echo;
rem echo ---------------------------------------
rem echo TESTING CYBAMAN Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d cybaman -p %EPICS_KIT_ROOT%\ioc\master\CYBAMAN\iocBoot\iocCYBAMAN-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING CYBAMAN Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d cybaman -p %EPICS_KIT_ROOT%\ioc\master\CYBAMAN\iocBoot\iocCYBAMAN-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem REM EGXCOLIM has no dev sim as it is an LvDCOM IOC
rem 
rem echo ---------------------------------------
rem echo TESTING EGXCOLIM Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d egxcolim -p %EPICS_KIT_ROOT%\ioc\master\EGXCOLIM\iocBoot\iocEGXCOLIM-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING IEG Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d ieg -p %EPICS_KIT_ROOT%\ioc\master\IEG\iocBoot\iocIEG-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
rem echo ---------------------------------------
rem 
rem echo ---------------------------------------
rem echo TESTING IEG Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d ieg -p %EPICS_KIT_ROOT%\ioc\master\IEG\iocBoot\iocIEG-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING HLG Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d hlg -p %EPICS_KIT_ROOT%\ioc\master\HLG\iocBoot\iocHLG-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING HLG Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d hlg -p %EPICS_KIT_ROOT%\ioc\master\HLG\iocBoot\iocHLG-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING EUROTHRM Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d eurotherm -p %EPICS_KIT_ROOT%\ioc\master\EUROTHRM\iocBoot\iocEUROTHRM-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING OSCILLATING COLLIMATOR Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d oscillating_collimator -p %EPICS_KIT_ROOT%\ioc\master\GALIL\iocBoot\iocGALIL-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING FERMI CHOPPER LIFTER Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d fermi_chopper_lifter -p %EPICS_KIT_ROOT%\ioc\master\GALIL\iocBoot\iocGALIL-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING MK3Chopper Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d mk3chopper -p %EPICS_KIT_ROOT%\ioc\master\MK3CHOPR\iocBoot\iocMK3CHOPR-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING MK3Chopper Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -d mk3chopper -p %EPICS_KIT_ROOT%\ioc\master\MK3CHOPR\iocBoot\iocMK3CHOPR-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING GEMORC Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d gemorc -p %EPICS_KIT_ROOT%\ioc\master\GEMORC\iocBoot\iocGEMORC-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING GEMORC Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d gemorc -p %EPICS_KIT_ROOT%\ioc\master\GEMORC\iocBoot\iocGEMORC-IOC-01
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING SKF MB350 Dev Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -d skf_mb350_chopper -p %EPICS_KIT_ROOT%\ioc\master\SKFMB350\iocBoot\iocSKFMB350-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
rem echo ---------------------------------------
rem echo;
rem 
rem echo ---------------------------------------
rem echo TESTING SKF MB350 Rec Sim
rem call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d skf_mb350_chopper -p %EPICS_KIT_ROOT%\ioc\master\SKFMB350\iocBoot\iocSKFMB350-IOC-01
rem 
rem echo ---------------------------------------
rem echo;
