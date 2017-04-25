# EPICS-IOC_Test_Framework

A framework for testing the functionality of IOCs using Lewis in place of real hardware.
This uses the Python unittest module to test setting and reading PV values etc. to check that the IOC responds correctly.

Note: the unittest module is used for convenience. The tests themselves are not strictly unit tests, so it is okay to deviate a little from unit testing best practises.

## How to run

NOTE: currently you **must** use the genie_python installation of Python.

It recommended that you don't have the server side of IBEX running then testing an IOC.

The command-line options are:
```
-pf = the instrument prefix, for example: IN:DEMO [REQUIRED]
-d = the name of the device in Lewis, for example: julabo
-p = the full path to the directory containing the st.cmd for the IOC
-e = the full path to the Lewis executable
-ep = the Lewis protocal to use. This is optional, currently it is only the julabo that requires the specific protocol to be set
-r = run in record simulation mode, this does not require Lewis
```


### Emulation mode:

From the command-line, the IOC and Lewis settings can be specified, for example:

```
> python.exe run_tests.py -pf IN:DEMO -d julabo -p C:\Instrument\Apps\EPICS\ioc\master\JULABO\iocBoot\iocJULABO-IOC-01 -e c:\CodeWorkspaces\GitHub\my_plankton\plankton\lewis.py -ep julabo-version-1
```


### Record simulation mode

To run in record simulation mode (does not require Lewis) use the -r option, for example:

```
> python.exe run_tests.py -pf IN:DEMO -r -d julabo -p C:\Instrument\Apps\EPICS\ioc\master\JULABO\iocBoot\iocJULABO-IOC-01
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

