# EPICS-IOC_Test_Framework

A framework for testing the functionality of IOCs using Lewis in place of real hardware.
This uses the Python unittest module to test setting and reading PV values etc. to check that the IOC responds correctly.

Note: the unittest module is used for convenience. The tests themselves are not strictly unit tests, so it is okay to deviate a little from unit testing best practises.

## How to run

NOTE: currently you **must** use the genie_python installation of Python because it allows you to access the python wrapper for EPICS Channel access.

It recommended that you don't have the server side of IBEX running when testing an IOC.

### Running all tests

To run all the tests in the test framework, use:

```
C:\Instrument\Apps\EPICS\config_env.bat
python run_tests.py
```

There is a batch file which does this for you, called `run_tests.bat`

### Running specific tests

Specify the test modules you want to run via the `-tm` argument:

```
python run_tests.py -tm instron_stress_rig amint2l  # Will run the stress rig tests and then the amint2l tests.
```

The argument is the name of the module containing the tests. This is the same as the name of the file in the `tests` directory, with the `.py` extension removed.

## Troubleshooting 

If all tests are failing then it is likely that the PV prefix is incorrect.
If a large percentage of tests are failing then it may that the macros in the IOC are not being set properly for the testing framework.

In most cases it requires inspecting what the IOC is doing, to do that one needs to edit the ioc_launcher.py file to remove the redirection of stdout, stdin and stderr. This will mean that the IOC will dump all its output to the console, so it will then be possible to scroll through it to check the prefix and macros are set correctly.

Note: in this mode the IOC will not automatically terminate after the tests have finished, this means it is possible to run diagnostic commands in the IOC, such as `dbl` etc.

## Adding testing for an IOC

### Modifying the IOC

For newer IOCs these steps may not be necessary as the st.cmd will be auto-generated to contain them.

st.cmd (or st-common.cmd) should be modified to use the EMULATOR_PORT macro in DEVSIM mode:
```
## For unit testing:
$(IFDEVSIM) drvAsynIPPortConfigure("$(DEVICE)", "localhost:$(EMULATOR_PORT=)")
```
The configurating of the real device should have macros guarded it to stop it trying to connect to the real device when under test.
```
## For real device use:
$(IFNOTDEVSIM) $(IFNOTRECSIM) drvAsynSerialPortConfigure("L0", "$(PORT=NO_PORT_MACRO)", 0, 0, 0, 0)
$(IFNOTDEVSIM) $(IFNOTRECSIM) asynSetOption("L0", -1, "baud", "$(BAUD=9600)")
$(IFNOTDEVSIM) $(IFNOTRECSIM) asynSetOption("L0", -1, "bits", "$(BITS=8)")
$(IFNOTDEVSIM) $(IFNOTRECSIM) asynSetOption("L0", -1, "parity", "$(PARITY=none)")
$(IFNOTDEVSIM) $(IFNOTRECSIM) asynSetOption("L0", -1, "stop", "$(STOP=1)")
```

### Adding a suite of tests

To add a another suite of tests:
* Create a Python file. This no longer has to have a specific name, but try to give it a name similar to the IOC and emulator so that it is easy to find.
* Ensure your test suite has the essential attributes `IOCS` and `TEST_MODES` (see below for more details)
* Create a test class (deriving from `unittest.TestCase`) in your module. This no longer has to have a specific name. You can have multiple test classes within a test module, all of them will be executed. 
* Fill the class with tests (see below).
* Add your new tests to run_all_tests.bat, this is the easiest way to run your new tests.

### The `IOCS` attribute

The `IOCS` attribute tells the test framework which IOCs need to be launched. Any number of IOCs are allowed. The `IOCS` attribute should be a list of dictionaries, where each dictionary contains information about one IOC/emulator combination. 

Essential attributes:
`name`: The IOC name of the IOC to launch, e.g. `GALIL_01`.
`directory`: The directory containing `runIoc.bat` for this IOC.

Essential attributes in devsim mode:
`emulator`: The name of the lewis emulator for this device.

Optional attributes:
`macros`: A dictionary of macros. Defaults to an empty dictionary (no additional macros)
`emulator_protocol`: The lewis protocol to use. Defaults to `stream`, which is used by the majority of ISIS emulators.
`emulator_path`: Where to find the lewis emulator for this device. Defaults to `EPICS/support/DeviceEmulator/master`
`emulator_package`: The package containing this emulator. Equivalent to Lewis' `-k` switch. Defaults to `lewis_emulators`

Example:

```python
IOCS = [
    {
        "name": "IOCNAME_01",
        "directory": get_default_ioc_dir("IOCNAME"),
        "macros": {
            "MY_MACRO": "My_value",
        },
        "emulator": "my_emulator_name",
    },
]
```

### The `TEST_MODES` attribute

This is a list of test modes to run this test suite in. A list of available test modes can be found in `utils\test_modes.py`. Currently these are RECSIM and DEVSIM.

Example:
```python
TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]
```

### Structure of a test

```python
class MydeviceTests(unittest.TestCase):
    # Runs before every test
    def setUp(self):
        # Grab a reference to the ioc and lewis
        self._lewis, self._ioc = get_running_lewis_and_ioc(“mydevice", "IOCNAME_01")
        # Setup channel access with a default timeout of 20 seconds and a IOC prefix of "IOCNAME_01"
        self.ca = ChannelAccess(default_timeout=20, device_prefix="IOCNAME_01")
        # Wait for a PV to be available – the IOC may take some time to start
        self.ca.wait_for(“DISABLE", timeout=30)
        
    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        # Assert that a PV has a particular value (prefix prepended automatically)          
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")
```
Try to use GIVEN_WHEN_THEN test naming wherever appropriate

### Setting values

1) Set via channel access:
```python
self.ca.set_pv_value("PRESSURE:SP", value)
```

2) Set via Lewis backdoor:
```python
self._lewis.backdoor_set_on_device("pressure", value)
```
* This is an “on-the-fly” modification of the device’s internal parameters
* Use this to set values that you wouldn’t be able to set via the IOC
* Can be useful to check the IOC’s response to error conditions

### Assertions

A number of custom assert statements are available in the test framework:
* `assert_that_pv_is `
  * Checks that a PV has a particular value (exact).
* `assert_that_pv_is_number`
  * Checks that a PV is a number, within a specified tolerance.
* `assert_that_pv_is_integer_between`
  * Checks that a PV is an integer between two specified bounds.
* `assert_pv_alarm_is`
  * Checks that a PV has a particular alarm state. 
* `assert_setting_setpoint_sets_readback`
  * Checks that a PV is a particular value after the relevant setpoint is changed.

If you find yourself needing other assert functions, please add them!

### Skipping tests in RECSIM

RECSIM is not as advanced as DEVSIM – for any reasonably complex emulator, the emulator will have some functionality which RECSIM doesn’t. Tests that require Lewis will error in RECSIM mode.

To skip these tests in RECSIM, add the following annotation to tests which shouldn't be run in RECSIM mode:
```python
@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
def test_GIVEN_condition_WHEN_thing_is_done_THEN_thing_happens(self):
    # Some functionality which doesn’t exist in recsim goes here
```
Any test which includes a Lewis backdoor command MUST have this annotation, otherwise it will error because it can’t find lewis in RECSIM mode.

### Avoiding tests affecting other tests

* When run by the IOC test framework, the IOC + emulator state persists between tests
* For simple tests/emulators this is not typically an issue, but for complex emulators this can cause tests to pass when run on their own but fail when run as part of a suite, or fail intermittently. This can be very hard to debug!
* Solution is to ensure a consistent startup state in the setUp method of the tests. 
This will run before each test, and it should “reset” all relevant properties of the device so that each test always starts from a consistent starting state
* Doing lots in the setup method will make the tests run a bit slower – this is preferable to having inconsistently passing tests!

### Parameterised tests
You can create tests which check a few values, e.g. boundaries, negative numbers, zero, floats and integers (if applicable to the device):

```python
def test_WHEN_speed_setpoint_is_set_THEN_readback_updates(self):
    for speed in [0, 0.65, 600]:
        self.ca.set_pv_value("SPEED:SP", speed)
        self.ca.assert_that_pv_is("SPEED:SP:RBV", speed)
```
Testing different types of values can quickly catch simple errors in the IOC’s records or protocol file, for example accidentally having a %i (integer) instead of %d (double) format converter.

### Rounding errors

For a non-trivial IOC you might get rounding errors, e.g. setpoint = 2.5, readback = 2.4997. To avoid this use the custom assert `assert_that_pv_is_number` with a tolerance:

```python
def test_WHEN_speed_setpoint_is_set_THEN_readback_updates(self):
    self.ca.set_pv_value("SPEED:SP", speed)
    self.ca.assert_that_pv_is_number("SPEED:SP:RBV", speed, tolerance=0.01)

```

### PINI records

If you have a record which is only processed at initialization (i.e. PINI=Yes, SCAN=Passive), one can test this by forcing it to process:

```python
def test_ioc_name(self):
    self._lewis.backdoor_set_on_device("name", “new_name”)
    # Force record to process and therefore get new value from emulator:
    self.ca.set_pv_value(“NAME.PROC", 1)
    self.ca.assert_that_pv_is(“NAME", “new_name")
```

### Macros

If your IOC needs a macro or macros set up in the test this is easy to do. Add to the test file the constant `MACROS` 
which should be a dictionary of macro names and their values. 
 For instance the amint2l needs an internal address set the macro for this is `ADDR` and the address is a number so at the top of
  the test file the following appears:
```python
    # MACROS to use for the IOC
    MACROS = {"ADDR": ADDRESS}
```
The way this works in the test framework is that when the test is loaded the macros are handed to the ioc
launcher. The launcher writes them into a file placed in the var dir and the ioc reads them from there.

### Wait For IOC to Start and IOC Prefix

When the IOC is started it can be made to wait until the pv `DISABLE` exist; if it doesn't exist after 30s then the 
tests will be stopped. To enable this option simply place in the test file the constant `DEVICE_PREFIX` which has the IOC
 prefix in. So for instance in the amint2l the device prefix is `AMINT2l_01` so in the header:
 ```python
     # Device prefix
     DEVICE_PREFIX = "AMINT2L_01"
```
If you want this in all your `ChannelAccess` interaction then I suggest passing it into the constructor, eg:
 ```python
     def setUp(self):
        ...
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
```
Then to assert that the pv `<inst prefix>:AMINT2L_01:PRESSURE` is 1 use:
```python
    self.ca.assert_that_pv_is("PRESSURE", 1)
```
### Logging

The IOC test framework writes logs to C:\Instrument\Var\logs\IOCTestFramework

You can force extra debug output by:
* Adding `@has_log` at the top of the class
* Using `self.log.debug("message")`
* `log.info`, `log.warning` and `log.error` are also available
