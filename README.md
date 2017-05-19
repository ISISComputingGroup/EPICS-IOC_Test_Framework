# EPICS-IOC_Test_Framework

A framework for testing the functionality of IOCs using Lewis in place of real hardware.
This uses the Python unittest module to test setting and reading PV values etc. to check that the IOC responds correctly.

Note: the unittest module is used for convenience. The tests themselves are not strictly unit tests, so it is okay to deviate a little from unit testing best practises.

## How to run

NOTE: currently you **must** use the genie_python installation of Python because it allows you to access the python wrapper for EPICS Channel access.

It recommended that you don't have the server side of IBEX running then testing an IOC.

The command-line options are split into groups:

- `-l`, `--list-devices`    List available devices that can be tested.

### all modes
- `-pf PREFIX`, `--prefix PREFIX` The instrument prefix which will be prefixed to all PVs; e.g. TE:NDW1373
- `-d DEVICE`, `--device DEVICE` Device type to test.
- `-p IOC_PATH`, `--ioc-path IOC_PATH` The path to the folder containing the IOC's st.cmd. It will run runIOC.bat st.cmd.

### Dev simulation mode
- `-e EMULATOR_PATH`, `--emulator-path EMULATOR_PATH` The path which contains lewis and lewis-control executables
- `-ep EMULATOR_PROTOCOL`, `--emulator-protocol EMULATOR_PROTOCOL` The Lewis protocal to use (optional)
- `-ea EMULATOR_ADD_PATH`, `--emulator-add-path EMULATOR_ADD_PATH` Add path where device packages exist for the emulator.
- `-ek EMULATOR_DEVICE_PACKAGE`, `--emulator-device-package EMULATOR_DEVICE_PACKAGE` device package to use to perform the emulation

### Rec simulation mode

- `-r`, `--record-simulation` Use record simulation rather than emulation (optional)
- `--var-dir VAR_DIR` Directory in which to create a log dir to write log file to and directory in which to create tmp dir which contains environments variables for the IOC. Defaults to environment variable ICPVARDIR and current dir if empty.

### Emulation mode:

From the command-line in the IocTestFramework directory, the IOC and Lewis settings can be specified, for example:

```
> python.exe run_tests.py -pf %MYPVPREFIX% -d julabo -p C:\Instrument\Apps\EPICS\ioc\master\JULABO\iocBoot\iocJULABO-IOC-01 -e c:\CodeWorkspaces\GitHub\my_plankton\plankton\lewis.py -ep julabo-version-1
```


### Record simulation mode

To run in record simulation mode (does not require Lewis) use the -r option, for example:

```
> python.exe run_tests.py -pf IN:DEMO -r -d julabo -p C:\Instrument\Apps\EPICS\ioc\master\JULABO\iocBoot\iocJULABO-IOC-01 -pf %MYPVPREFIX%
```


## Adding more IOCs

1. Create a Python file with the same name as the Lewis device (for example: julabo, linkam_t95). This should be lowercase.
2. Create a class in it with the same name as the file but with the first letter capitialised and "Tests" appended (for example: Linkam_t95Tests).
3. Fill the class with tests.
4. Done!

## Troubleshooting 

If all tests are failing then it is likely that the PV prefix is incorrect.
If a large percentage of tests are failing then it may that the macros in the IOC are not being set properly for the testing framework.

In most cases it requires inspecting what the IOC is doing, to do that one needs to edit the ioc_launcher.py file to remove the redirection of stdout, stdin and stderr. This will mean that the IOC will dump all its output to the console, so it will then be possible to scroll through it to check the prefix and macros are set correctly.

Note: in this mode the IOC will not automatically terminate after the tests have finished, this means it is possible to run diagnostic commands in the IOC, such as `dbl` etc.

