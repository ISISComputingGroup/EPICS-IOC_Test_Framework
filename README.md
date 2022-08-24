# EPICS-IOC_Test_Framework

A framework for testing the functionality of IOCs using [Lewis](https://lewis.readthedocs.io/en/latest/) in place of real hardware.
This uses the Python unittest module to test setting and reading PV values etc. to check that the IOC responds correctly.

Note: the unittest module is used for convenience. The tests themselves are not strictly unit tests, so it is okay to deviate a little from unit testing best practises.

## How to run

NOTE: currently you **must** use the genie_python installation of Python because it allows you to access the python wrapper for EPICS Channel access.

It recommended that you don't have the server side of IBEX running when testing an IOC.

### Running all tests

To run all the tests that are bundled in the test framework, use:

```
C:\Instrument\Apps\EPICS\config_env.bat
```
Then `cd` to `C:\Instrument\Apps\EPICS\support\IocTestFramework\master` and use:
```
python run_tests.py
```

There is a batch file which does this for you, called `run_all_tests.bat`. If you are already in an EPICS 
terminal you can call `make ioctests`, but it is best to do this from the directory above this as you
will not see test output until all complete - see comments in `Makefile`

### Running tests in modules

You can run tests in specific modules using the `-t` argument as follows:

```
python run_tests.py -t instron_stress_rig amint2l  # Will run the stress rig tests and then the amint2l tests.
```

The argument is the name of the module containing the tests. This is the same as the name of the file in the `tests` 
directory, with the `.py` extension removed.

### Running tests in classes

You can run classes of tests in modules using the `-t` argument as follows:

```
python run_tests.py -t sp2xx.RunCommandTests # This will run all the tests in the RunCommandTests class in the sp2xx module. 
```

The argument is the "dotted name" of the class containing the tests. The dotted name takes the form `module.class`.
You can run the tests in multiple classes in different modules.

### Running tests by name

You can run tests by name using `-t` argument as follows:

```
python run_tests.py -t sp2xx.RunCommandTests.test_that_GIVEN_an_initialized_pump_THEN_it_is_stopped # This will run the test_that_GIVEN_an_initialized_pump_THEN_it_is_stopped test in the RunCommandTests class in the sp2xx module. 
```

The argument is the "dotted name" of the test containing the tests. The dotted name takes the form `module.class.test`.
You can run multiple tests from multiple classes in different modules.

### Running tests with failfast

Running tests with `-f` argument will cause tests to run normally _until_ the first test fails, upon which it will quit testing and provide the usual output for a failed test.

>`python run_tests.py -f` will cause all IOC tests to run, up until the first one fails. 

### Running tests in a given path

By default the framework searches for tests inside `.\tests\`. If you wish to specify tests in another directory you can use the `-tp` flag.

>`python run_tests.py -tp C:\my_ioc_tests` will run tests in the `my_ioc_tests` folder.

### Run test but Ask before starting the tests but after the IOC and emmulator are running

It is sometimes useful to attach a debugger to the test using this option means that the framework will ask to run tests before it starts the setup for the test.
This gives you time to attach a debugger. It also allows you an easy way to set up the system with emmulator and ioc attached to each other for unscripted testing.

>  `python run_tests.py -a` will ask if you want to run test before it runs them.

### Run test in a specific mode

Sometimes you might want to run all the tests only in RECSIM or only in DEVSIM. You can do this by doing:

>  `python run_tests.py -tm RECSIM`

### Run test and emulator from specific directory

For newer IOCs the emulator and tests live in the support folder of the IOC. To specify this to the test framework
you can use: 

>  `python run_tests.py  --test_and_emulator C:\Instrument\Apps\EPICS\support\CCD100\master\system_tests`

## Troubleshooting 

If all tests are failing then it is likely that the PV prefix is incorrect.
If a large percentage of tests are failing then it may that the macros in the IOC are not being set properly for the testing framework.

It is important to explicitly set each of the macro values for an IOC in its IOC test module. This is to prevent macros set in a configuration from interfering with the values used in the test, even if they are the default values.

To inspect the IOC settings in further detail, one needs to edit the ioc_launcher.py file to remove the redirection of stdout, stdin and stderr. This will mean that the IOC will dump all its output to the console, so it will then be possible to scroll through it to check the prefix and macros are set correctly.

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
* Create a test class (deriving from `unittest.TestCase`) in your module and fill it with tests. This no longer has to have a specific name. You can have multiple test classes within a test module, all of them will be executed. 
* Done!

### The `IOCS` attribute

The `IOCS` attribute tells the test framework which IOCs need to be launched. Any number of IOCs are allowed. The `IOCS` attribute should be a list of dictionaries, where each dictionary contains information about one IOC/emulator combination. 

Essential attributes:
- `name`: The IOC name of the IOC to launch, e.g. `GALIL_01`.
- `directory`: The directory containing `runIoc.bat` for this IOC.

Essential attributes in devsim mode:
- `emulator`: The name of the lewis emulator for this device. (or pass `emulators` instead)

Optional attributes:
- `macros`: A dictionary of macros. Defaults to an empty dictionary (no additional macros)
- `inits` : A dictionary of initialisation values for PVs in this IOC. Defaults to an empty dictionary.
- `custom_prefix` : A custom PV prefix for this IOC in case this is different from the IOC name (example: custom prefix `MOT` for IOC `GALIL_01`)
- `emulator_protocol`: The lewis protocol to use. Defaults to `stream`, which is used by the majority of ISIS emulators.
- `emulator_path`: Where to find the lewis emulator for this device. Defaults to `EPICS/support/DeviceEmulator/master`
- `emulator_package`: The package containing this emulator. Equivalent to Lewis' `-k` switch. Defaults to `lewis_emulators`
- `emulator_launcher_class`: Used if you want to launch an emulator that is not Lewis see [other emulators.](#other-emulators)
- `pre_ioc_launch_hook`: Pass a callable to execute before this ioc is launched. Defaults to do nothing
- `emulators`: Pass a list of `TestEmulatorData` objects to launch multiple lewis emulators.

Example:

```python
IOCS = [
    {
        "name": "IOCNAME_01",
        "directory": get_default_ioc_dir("IOCNAME"),
        "macros": {
            "MY_MACRO": "My_value",
        },
        "inits": {
            "MYPV:SP": 5.0
        },
        "emulator": "my_emulator_name",
    },
]
```

#### Changing the IOC number

If you want a to run the IOC tests against a different number IOC, e.g. "IOCNAME_02", 
you need to change the following:

1. Set `DEVICE_PREFIX` to `IOCNAME_02`.
1. Change the "name" property of the IOC dictionary to `IOCNAME_02`.
1. Pass the keyword argument `iocnum=2` to `get_default_ioc_dir()`.

The test framework now start the `IOCNAME_02` IOC to run the tests against.

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
        self.ca = ChannelAccess(default_timeout=20, device_prefix="IOCNAME_01", default_wait_time=0.0)
        # Wait for a PV to be available – the IOC may take some time to start
        self.ca.wait_for(“DISABLE", timeout=30)
        
    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        # Assert that a PV has a particular value (prefix prepended automatically)          
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")
```
Try to use GIVEN_WHEN_THEN test naming wherever appropriate. By default `ChannelAccess` will wait 1 second after every set, but this can dramatically slow down tests. Newer tests should override this default using `default_wait_time=0.0` and only sleep where definitely required.

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
* `assert_that_pv_monitor_is`
  * Checks that a PV has issued a monitor for a pv and that the value is as set. This used in a with:
      ```
      with self.ca.assert_that_pv_monitor_is("MY:PV:NAME", expected_value):
            self.ca.set_pv_value("MY:PV:NAME:SP", 1)
      ```
* `assert_that_pv_monitor_is_number`
  * Checks that a PV has issued a monitor for a pv and that it is a number, within a specified tolerance. Used in a similar way to `assert_that_pv_monitor_is`

* `assert_that_emulator_value_is`
  * Checks that an emulator property has the expected value or that it becomes the expected value within the timeout.

If you find yourself needing other assert functions, please add them!

Note: If using PyCharm, you can add code completeion/suggestions for function names by opening the folder `IoCTestFramework`, rightclick on `master` in the project explorer on the left, and selecting `Mark Directory as... > Sources Root`. 

### Testing device disconnection behaviour 
To safely test disconnection behaviour, you can use the emulator utility function `backdoor_simulate_disconnected_device`, with parameters `(self, emulator_property="connected")`. 
This has been written in place of using the below to assert an alarm is INVALID. 
```python 
self.lewis.backdoor_set_on_device("connected", False)
```
When writing these tests to check alarm behaviour with a disconnected device, you may want to consider asserting alarms are clear before and after to ensure the test is rigorous.
Here you can see a generic template to use the function:
```python
def test_WHEN_device_disconnects_THEN_pvs_go_into_alarm(self, _, pv):
        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)

        with self._lewis.backdoor_simulate_disconnected_device():
            self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.INVALID, timeout=30)

        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE, timeout=30)
```

### Skipping tests in RECSIM

RECSIM is not as advanced as DEVSIM – for any reasonably complex emulator, the emulator will have some functionality which RECSIM doesn’t. Tests that require Lewis will error in RECSIM mode.

To skip these tests in RECSIM, add the following annotation to tests which shouldn't be run in RECSIM mode:
```python
from utils.testing import skip_if_recsim

@skip_if_recsim("In rec sim this test fails")
def test_GIVEN_condition_WHEN_thing_is_done_THEN_thing_happens(self):
    # Some functionality which doesn’t exist in recsim goes here
```
Any test which includes a Lewis backdoor command MUST have this annotation, otherwise it will error because it can’t find lewis in RECSIM mode.

There is also an equivalent `skip_if_devsim` annotation which can be used.

If you do not call the decorator with a message as its first argument, the test will fail with a message like:
```
Traceback (most recent call last):
  File "C:\Instrument\Apps\EPICS\support\IocTestFramework\master\utils\testing.py", line 93, in decorator
    @functools.wraps(func)
  File "C:\Instrument\Apps\Python\lib\functools.py", line 33, in update_wrapper
    setattr(wrapper, attr, getattr(wrapped, attr))
AttributeError: 'obj' object has no attribute '__name__'
```

This can be avoided by calling the decorator like ` @skip_if_recsim("In rec sim this test fails") `

### Avoiding tests affecting other tests

* When run by the IOC test framework, the IOC + emulator state persists between tests
* For simple tests/emulators this is not typically an issue, but for complex emulators this can cause tests to pass when run on their own but fail when run as part of a suite, or fail intermittently. This can be very hard to debug!
* Solution is to ensure a consistent startup state in the setUp method of the tests. 
This will run before each test, and it should “reset” all relevant properties of the device so that each test always starts from a consistent starting state
* Doing lots in the setup method will make the tests run a bit slower – this is preferable to having inconsistently passing tests!
* When creating base classes for tests please have your base class inherit from `object` and your subclasses inherit
from your base class and `unittest.TestCase`. See [Python unit tests with base and sub class](https://stackoverflow.com/questions/1323455/python-unit-test-with-base-and-sub-class)
for more discussion.

### Parameterised tests
You can create tests which check a few values, e.g. boundaries, negative numbers, zero, floats and integers (if applicable to the device):

```python
def test_WHEN_speed_setpoint_is_set_THEN_readback_updates(self):
    for speed in [0, 0.65, 600]:
        self.ca.set_pv_value("SPEED:SP", speed)
        self.ca.assert_that_pv_is("SPEED:SP:RBV", speed)
```
Testing different types of values can quickly catch simple errors in the IOC’s records or protocol file, for example accidentally having a %i (integer) instead of %d (double) format converter.

The above was the old way of parameterizing tests. After installing `parameterized` using pip, you can parameterize your tests so that a new test runs for each case. Documentation for parameterized can be found at https://github.com/wolever/parameterized.

Example code:

```python
@parameterized.expand([
        ("Pin_{}".format(i), i) for i in range(2, 8)
    ])
    def test_that_we_can_read_a_digital_input(self, _, pin):
        # Given
        pv = "PIN_{}".format(pin)
        self._lewis.backdoor_run_function_on_device("set_input_state_via_the_backdoor", [pin, "FALSE"])
        self.ca.assert_that_pv_is(pv, "FALSE")

        self._lewis.backdoor_run_function_on_device("set_input_state_via_the_backdoor", [pin, "TRUE"])

        # When:
        self.ca.process_pv(pv)

        # Then:
        self.ca.assert_that_pv_is(pv, "TRUE")
```

This runs a new test for each case with the name `test_that_we_can_read_a_digital_input_{j}_Pin_{i}` where `{j}` indexes the tests from `0` to `5` and `{i}` runs from `2` to `7`.

**Note:** Trying to run a single test using `-tn test_that_we_can_read_a_digital_input` will result in *no tests* being run. However, you can run a single test with the correct suffix, e.g `-tn test_that_we_can_read_a_digital_input_0_Pin_2` runs the test case with `pin = 2`.

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

## Other Emulators
 
 By default the test framework will run emulators written under the [Lewis](https://lewis.readthedocs.io/en/latest/) framework. However, in some cases you may want to run up a different emulator. This is useful if there is already an emulator provided by the device manufacture, as is the case for the mezei flipper and the beckhoff.
 
### Command Line Emulator

Other than Lewis this is currently the only other emulation method. It will run a given command line script and optionally wait for it to complete. To use it you should add the following to the `IOCS` [attribute](#the-iocs-attribute).

Essential attributes:
- `emulator_launcher_class`: Use `CommandLineEmulatorLauncher` to use this emulator.
- `emulator_command_line`: The script to run on the command line e.g. `python my_emulator.py`

Optional attributes:
- `emulator_wait_to_finish`: If `true` wait for the process to complete and return before running the tests. This can be useful if the emulator will start up as a background process. It defaults to `false`.

### Adding an Emulator Type

To add an additional emulator type you should create a class in `emulator_launcher.py` that inherits from `EmulatorLauncher`.

### Manager Mode

The utils testing module has a decorator for turning manager mode on and can be used like:
```python
    from utils.testing import ManagerMode
    def test_something(self):
        with ManagerMode(self.ca):
            # Now in manager mode
            self.ca.set_pv_value(LOCKED_PV, value)
        # Now not in manager mode
```

To run this you will need the `INSTETC` IOC running and so the following must be added to your list of IOCs:
```python
    {
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC")
    }
```

### Launching multiple emulators 

Use the `emulators` `IOCS` attribute instead of `emulator` and pass through a list of `TestEmulatorData` objects. 

See hlx503 tests and example:

```python
from utils.free_ports import get_free_ports
from utils.emulator_launcher import TestEmulatorData
from utils.ioc_launcher import get_default_ioc_dir

num_of_lksh218_emulators = 2
lksh218_ports = get_free_ports(num_of_lksh218_emulators)
num_of_tpg300_emulators = 2
tpg300_ports = get_free_ports(num_of_tpg300_emulators)

IOCS = [
  {
    "name": "LKSH218_01",
    "directory": get_default_ioc_dir("LKSH218"),
    "macros": {
      "MY_MACRO": "My_value",
    },
    "emulators": [TestEmulatorData("lksh218", lksh218_ports[i], i) for i in range(num_of_lksh218_emulators)],
  },
  {
    "name": "TPG300_01",
    "directory": get_default_ioc_dir("TPG300"),
    "macros": {
      "MY_MACRO": "My_value",
    },
    "emulators": [TestEmulatorData("tpg300", tpg300_ports[i], i) for i in range(num_of_tpg300_emulators)],
  },
]
```

## My test doesn't always pass when it should

### Incorrect behaviour when restarting an ioc (autosave)

IOCs will often autosave values to be restored on restart. Autosaving is done periodically on a timer loop (potentially 30 seconds), so a changed value will not immediately be written to the file for use on restart. If your test involves restarting an IOC and checking a particular value or behaviour is preverved, then you will need to be aware of the autosave frequency. Waiting > 30 seconds will probably do, but we should look to provide a convenience function to help e.g. "wait for next autosave". This may not be trivial though as pvs could be in different autosave sets with different save frequencies. 

## Incorrect behaviour when device is dicconnected (scanning / lockTimeout)

Is a lewis device is told to diconnect, then all future stream device calls will timeout after replyTimeout. A record set to process has lockTimeout seconds to start processing its first protcol "out" before timing out. If you disconnect a device in your ioc test and then want to see if e.g. a PV goes into an alarm start, you will need to make sure you give it at least `lockTimeout` seconds to enter its invalid state. `lockTimeout` is 5 seconds by default, but is configurable on a per device basis - see the stream device protocol file.      

