# EPICS-IOC_Test_Framework

A framework for testing IOCs using Lewis in place of real hardware.
This uses the Python unittest module to test setting and reading PV values to check that the IOC responds correctly.

Note: the unittest module is used for convenience. The tests themselves are not strictly unit tests.

## How to run

From the command-line, the IOC and Lewis settings can be specified, for example:

```
> python.exe run_tests.py -d julabo -p C:\Instrument\Apps\EPICS\ioc\master\JULABO\iocBoot\iocJULABO-IOC-01 -e c:\CodeWorkspaces\GitHub\my_plankton\plankton\lewis.py -ep julabo-version-1
```

The command-line options are:
```
-d = the name of the device in Lewis, for example: julabo
-p = the full path to the directory containing the st.cmd for the IOC
-e = the full path to the Lewis start script (lewis.py)
-ep = the Lewis protocal to use. This is optional, currently it is only the julabo that requires the specific protocol to be set
```

NOTE: it must use the genie_python installation of Python.

## Adding more IOCs

1. Create a Python file with the same name as the Lewis device (for example: julabo, linkam_t95). This should be lowercase.
2. Create a class in it with the same name as the file but with the first letter capitialised and "Tests" appended (for example: Linkam_t95Tests).
3. Fill the class with tests.
4. Done!