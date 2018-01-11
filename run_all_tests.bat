@echo off
REM Run all known tests using the IOC Testing Framework

SET CurrentDir=%~dp0

call "%~dp0..\..\..\config_env.bat"

echo ---------------------------------------
echo TESTING JULABO Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm julabo -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING JULABO Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm julabo
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING TPG26X Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm tpg26x -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING TPG26X Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm tpg26x
echo ---------------------------------------
echo;
 
echo ---------------------------------------
echo TESTING AMINT2L Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm amint2l -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING AMINT2L Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm amint2l
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING INSTRON Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm instron_stress_rig -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING INSTRON Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm instron_stress_rig
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING AG33220A Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -tm ag33220a -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING FERMI CHOPPER Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm fermichopper -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING FERMI CHOPPER Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm fermichopper
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING XYARMBEAMSTOP Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm xyarmbeamstop
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING KEPCO Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -tm kepco -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING KEPCO Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -tm kepco
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING TDK_LAMBDA_GENESYS Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -tm tdk_lambda_genesys -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING TDK_LAMBDA_GENESYS Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -tm tdk_lambda_genesys
echo ---------------------------------------
echo;

rem REM SAMPOS has no dev sim as it is an LvDCOM IOC

echo ---------------------------------------
echo TESTING SAMPOS Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm sampos
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING RKNPS Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm rknps -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING RKNPS Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm rknps
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING CYBAMAN Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -tm cybaman -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING CYBAMAN Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -tm cybaman
echo ---------------------------------------
echo;

REM EGXCOLIM has no dev sim as it is an LvDCOM IOC

echo ---------------------------------------
echo TESTING EGXCOLIM Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -tm egxcolim
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING IEG Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -tm ieg -e %PYTHONDIR%\Scripts
echo ---------------------------------------

echo ---------------------------------------
echo TESTING IEG Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -tm ieg
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING HLG Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -tm hlg -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING HLG Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -tm hlg
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING EUROTHRM Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm eurotherm -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING EUROTHRM Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -tm eurotherm
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING OSCILLATING COLLIMATOR Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm oscillating_collimator
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING FERMI CHOPPER LIFTER Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm fermi_chopper_lifter
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING MK3Chopper Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -tm mk3chopper -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING MK3Chopper Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -r -tm mk3chopper
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING GEMORC Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -tm gemorc -e %PYTHONDIR%\Scripts
echo;

echo ---------------------------------------
echo TESTING GEMORC Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX% -tm gemorc
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING SKF MB350 Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX%  -tm skf_mb350_chopper -e %PYTHONDIR%\Scripts
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING SKF MB350 Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX% -tm skf_mb350_chopper
echo ---------------------------------------
echo;
