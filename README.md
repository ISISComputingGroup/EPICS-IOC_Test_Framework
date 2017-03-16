# EPICS-IOC_Test_Framework

A framework for testing the functionality of IOCs using Lewis in place of real hardware.
This uses the Python unittest module to test setting and reading PV values etc. to check that the IOC responds correctly.

Note: the unittest module is used for convenience. The tests themselves are not strictly unit tests, so it is okay to deviate a little from unit testing best practises.

## How to run

NOTE: you **must** use the genie_python installation of Python.

The command-line options are:
```
-d = the name of the device in Lewis, for example: julabo
-p = the full path to the directory containing the st.cmd for the IOC
-e = the full path to the Lewis executable
-ep = the Lewis protocal to use. This is optional, currently it is only the julabo that requires the specific protocol to be set
-r = run in record simulation mode, this does not require Lewis
```


### Emulation mode:

From the command-line, the IOC and Lewis settings can be specified, for example:

```
> python.exe run_tests.py -d julabo -p C:\Instrument\Apps\EPICS\ioc\master\JULABO\iocBoot\iocJULABO-IOC-01 -e C:\Instrument\Apps\Python\Scripts\lewis.exe -ep julabo-version-1
```


### Record simulation mode

To run in record simulation mode (does not require Lewis) use the -r option, for example:

```
> python.exe run_tests.py -r -d julabo -p C:\Instrument\Apps\EPICS\ioc\master\JULABO\iocBoot\iocJULABO-IOC-01
```


## Adding more IOCs

1. Create a Python file with the same name as the Lewis device (for example: julabo, linkam_t95). This should be lowercase.
2. Create a class in it with the same name as the file but with the first letter capitialised and "Tests" appended (for example: Linkam_t95Tests).
3. Fill the class with tests.
4. Done!
