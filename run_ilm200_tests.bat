echo ---------------------------------------
echo TESTING ILM 200 Rec Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -r -pf %MYPVPREFIX%  -d ilm200 -p %EPICS_KIT_ROOT%\ioc\master\ILM200\iocBoot\iocILM200-IOC-01
echo ---------------------------------------
echo;

echo ---------------------------------------
echo TESTING SM300 Dev Sim
call %PYTHON% "%EPICS_KIT_ROOT%\support\IocTestFramework\master\run_tests.py" -pf %MYPVPREFIX% -d ilm200 -p %EPICS_KIT_ROOT%\ioc\master\ILM200\iocBoot\iocILM200-IOC-01 -e %PYTHONDIR%\Scripts -ea %EPICS_KIT_ROOT%\support\DeviceEmulator\master -ek lewis_emulators
echo ---------------------------------------
echo ;