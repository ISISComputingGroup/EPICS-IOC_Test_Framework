import itertools
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP, ProcServLauncher, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim

DEVICE_PREFIX = "LKSH340_01"
_EMULATOR_NAME = "lakeshore340"

THRESHOLDS_FILE = "Test1.txt"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LKSH340"),
        "emulator": _EMULATOR_NAME,
        "ioc_launcher_class": ProcServLauncher,
        "macros": {
            "EXCITATION_THRESHOLD_FILE": THRESHOLDS_FILE,
            "USE_EXCITATION_THRESHOLD_FILE": "YES",
        },
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


SENSORS = ["A", "B", "C", "D"]
TEST_TEMPERATURES = [0.0, 0.0001, 1.0001, 123.456]
TEST_READINGS = TEST_TEMPERATURES

PID_SETTINGS = ["P", "I", "D"]
PID_TEST_VALUES = TEST_TEMPERATURES

PID_MODES = [
    "Manual PID",
    "Zone",
    "Open Loop",
    "Autotune PID",
    "Autotune PI",
    "Autotune P",
]

LOOP_STATES = ["On", "Off"]

HEATER_PERCENTAGES = [0, 0.01, 12.34, 99.99, 100.0]
RANGES = ["0%", "0.01%", "0.1%", "1%", "10%", "100%"]
EXCITATIONS = [
    "Off",
    "30 nA",
    "100 nA",
    "300 nA",
    "1 uA",
    "3 uA",
    "10 uA",
    "30 uA",
    "100 uA",
    "300 uA",
    "1 mA",
    "10 mV",
    "1 mV",
]
TEMP_SP_EXCITATIONS = [
    {
        "TEMP:SP": 5.2,
        "THRESHOLDS:TEMP": 18.0,
        "THRESHOLDS:EXCITATION": "100 nA",
    },  # Gets last value from Test1.txt
    {"TEMP:SP": 15.3, "THRESHOLDS:TEMP": 15.0, "THRESHOLDS:EXCITATION": "1 mV"},
    {"TEMP:SP": 19.2, "THRESHOLDS:TEMP": 15.0, "THRESHOLDS:EXCITATION": "1 mV"},
    {"TEMP:SP": 300.8, "THRESHOLDS:TEMP": 20.0, "THRESHOLDS:EXCITATION": "30 nA"},
]

THRESHOLD_FILE_PV = "THRESHOLDS:FILE.VAL$"
THRESHOLD_FILE_PROC = "THRESHOLDS:_CALC.PROC"
THRESHOLD_EXCITATIONS_PV = "THRESHOLDS:EXCITATION"
EXCITATIONA_PV = "EXCITATIONA"
THRESHOLD_TEMP_PV = "THRESHOLDS:TEMP"
THRESHOLDS_ERROR_PV = "THRESHOLDS:ERROR"
THRESHOLDS_DELAY_CHANGE_PV = "THRESHOLDS:DELAY_CHANGE"
THRESHOLD_FILES_DIR = EPICS_TOP + "/support/lakeshore340/master/excitation_thresholds/"


class Lakeshore340Tests(unittest.TestCase):
    """
    Tests for the lakeshore 340 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(_EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=15)

    def test_WHEN_device_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(itertools.product(SENSORS, TEST_TEMPERATURES)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_temperature_set_via_backdoor_THEN_it_can_be_read_back(self, _, sensor, value):
        self._lewis.backdoor_set_on_device("temp_{}".format(sensor.lower()), value)
        self.ca.assert_that_pv_is_number("{}:TEMP".format(sensor.upper()), value)

    @parameterized.expand(parameterized_list(itertools.product(SENSORS, TEST_TEMPERATURES)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_measurement_set_via_backdoor_THEN_it_can_be_read_back(self, _, sensor, value):
        self._lewis.backdoor_set_on_device("measurement_{}".format(sensor.lower()), value)
        self.ca.assert_that_pv_is_number("{}:RDG".format(sensor.upper()), value)

    @parameterized.expand(parameterized_list(TEST_TEMPERATURES))
    def test_WHEN_tset_is_changed_THEN_readback_updates(self, _, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, readback_pv="A:TEMP:SP:RBV", set_point_pv="A:TEMP:SP"
        )

    @parameterized.expand(parameterized_list(itertools.product(PID_SETTINGS, PID_TEST_VALUES)))
    def test_WHEN_pid_settings_changed_THEN_can_be_read_back(self, _, setting, value):
        if setting == "D":
            value = int(value)  # Derivative is only allowed to take integer values.

        self.ca.assert_setting_setpoint_sets_readback(value, setting)

    @parameterized.expand(parameterized_list(PID_MODES))
    def test_WHEN_pid_settings_changed_THEN_can_be_read_back(self, _, mode):
        self.ca.assert_setting_setpoint_sets_readback(mode, "PIDMODE")

    @parameterized.expand(parameterized_list(LOOP_STATES))
    def test_WHEN_loop_turned_on_or_off_THEN_can_be_read_back(self, _, loopstate):
        self.ca.assert_setting_setpoint_sets_readback(loopstate, "LOOP")

    @parameterized.expand(parameterized_list(TEST_TEMPERATURES))
    def test_WHEN_max_temperature_set_THEN_can_be_read_back(self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "TEMP:MAX")

    @parameterized.expand(parameterized_list(HEATER_PERCENTAGES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_heater_power_set_via_backdoor_THEN_can_be_read_back(self, _, output):
        self._lewis.backdoor_set_on_device("heater_output", output)
        self.ca.assert_that_pv_is_number("OUTPUT", output)

    @parameterized.expand(parameterized_list(RANGES))
    def test_WHEN_heater_range_set_THEN_can_be_read_back(self, _, range):
        self.ca.assert_setting_setpoint_sets_readback(range, "RANGE")

    @parameterized.expand(parameterized_list(EXCITATIONS))
    def test_WHEN_excitation_a_set_THEN_can_be_read_back(self, _, excitation):
        self.ca.assert_setting_setpoint_sets_readback(excitation, "EXCITATIONA")

    @parameterized.expand(parameterized_list(EXCITATIONS))
    @skip_if_recsim
    def test_WHEN_excitation_set_by_backdoor_THEN_can_be_read_back(self, _, excitation):
        self._lewis.backdoor_set_on_device("excitationa", EXCITATIONS.index(excitation))
        self.ca.assert_that_pv_is("EXCITATIONA", excitation)

    def test_WHEN_use_valid_file_THEN_threshold_file_is_none(self):
        self.ca.assert_that_pv_is_path(THRESHOLD_FILE_PV, THRESHOLD_FILES_DIR + THRESHOLDS_FILE)
        self.ca.assert_that_pv_is(THRESHOLDS_ERROR_PV, "No Error")
        self.ca.assert_that_pv_is("THRESHOLDS:USE", "YES")

    def test_WHEN_do_not_use_file_THEN_threshold_file_is_not_set(self):
        with self._ioc.start_with_macros(
            {"USE_EXCITATION_THRESHOLD_FILE": "NO"}, pv_to_wait_for=THRESHOLD_FILE_PV
        ):
            self.ca.assert_that_pv_is_path("THRESHOLDS:USE", "NO")
            self.ca.assert_that_pv_is(THRESHOLDS_ERROR_PV, "No Error")

    def test_WHEN_initialise_with_incorrect_macro_THEN_pv_is_in_alarm(self):
        filename = "DoesNotExist.txt"
        with self._ioc.start_with_macros(
            {"EXCITATION_THRESHOLD_FILE": filename, "USE_EXCITATION_THRESHOLD_FILE": "YES"},
            pv_to_wait_for=THRESHOLD_FILE_PV,
        ):
            self.ca.assert_that_pv_is_path(THRESHOLD_FILE_PV, THRESHOLD_FILES_DIR + filename)
            self.ca.set_pv_value(THRESHOLD_FILE_PROC, 1)
            self.ca.assert_that_pv_is("THRESHOLDS:USE", "YES")
            self.ca.assert_that_pv_is(THRESHOLDS_ERROR_PV, "File Not Found")

    def test_WHEN_initialise_with_invalid_file_THEN_pv_is_in_alarm(self):
        filename = "InvalidLines.txt"
        with self._ioc.start_with_macros(
            {"EXCITATION_THRESHOLD_FILE": filename, "USE_EXCITATION_THRESHOLD_FILE": "YES"},
            pv_to_wait_for=THRESHOLD_FILE_PV,
        ):
            self.ca.assert_that_pv_is_path(THRESHOLD_FILE_PV, THRESHOLD_FILES_DIR + filename)
            self.ca.set_pv_value(THRESHOLD_FILE_PROC, 1)
            self.ca.assert_that_pv_is("THRESHOLDS:USE", "YES")
            self.ca.assert_that_pv_is(THRESHOLDS_ERROR_PV, "Invalid Lines In File")

    def reset_thresholds_values(
        self, thresholds_excitations, thresholds_temp, excitationa, error, delay_change, temp
    ):
        self.ca.assert_setting_setpoint_sets_readback(excitationa, EXCITATIONA_PV)
        self.ca.set_pv_value(THRESHOLD_TEMP_PV, thresholds_temp)
        self.ca.set_pv_value(THRESHOLD_EXCITATIONS_PV, thresholds_excitations)
        self.ca.set_pv_value(THRESHOLDS_DELAY_CHANGE_PV, delay_change)
        self.ca.set_pv_value(THRESHOLDS_ERROR_PV, error)
        self._lewis.backdoor_set_on_device("temp_a", temp)

    def assert_threshold_values(
        self,
        thresholds_excitations,
        thresholds_temp,
        excitationa,
        error,
        error_severity,
        delay_change,
    ):
        self.ca.assert_that_pv_is(THRESHOLD_EXCITATIONS_PV, thresholds_excitations)
        self.ca.assert_that_pv_is(THRESHOLD_TEMP_PV, thresholds_temp)
        self.ca.assert_that_pv_is(THRESHOLDS_DELAY_CHANGE_PV, delay_change)
        self.ca.assert_that_pv_is(THRESHOLDS_ERROR_PV, error)
        self.ca.assert_that_pv_alarm_is(THRESHOLDS_ERROR_PV, error_severity)
        self.ca.assert_that_pv_is(EXCITATIONA_PV, excitationa)

    @parameterized.expand(parameterized_list(TEMP_SP_EXCITATIONS))
    @skip_if_recsim
    def test_WHEN_set_temp_sp_THEN_thresholds_recalculated(self, _, temp_sp_excitations_map):
        new_temp_sp = temp_sp_excitations_map["TEMP:SP"]
        expected_thresholds_temp = temp_sp_excitations_map["THRESHOLDS:TEMP"]
        expected_thresholds_excitation = temp_sp_excitations_map["THRESHOLDS:EXCITATION"]
        # Reset pv values to test
        self.reset_thresholds_values("Off", 0, "Off", "No Error", "NO", new_temp_sp - 10)
        # Set setpoint
        self.ca.assert_setting_setpoint_sets_readback(
            new_temp_sp, readback_pv="A:TEMP:SP:RBV", set_point_pv="A:TEMP:SP"
        )
        # Confirm change is delayed but threshold temp is set
        self.assert_threshold_values(
            expected_thresholds_excitation,
            expected_thresholds_temp,
            "Off",
            "No Error",
            "NO_ALARM",
            "YES",
        )
        # Make temperature equal setpoint
        self._lewis.backdoor_set_on_device("temp_a", new_temp_sp)
        # Confirm Excitations is set correctly
        self.assert_threshold_values(
            expected_thresholds_excitation,
            expected_thresholds_temp,
            expected_thresholds_excitation,
            "No Error",
            "NO_ALARM",
            "NO",
        )

    @parameterized.expand(
        parameterized_list(
            [
                ("None.txt", "NO_ALARM", "No Error"),
                ("DoesNotExist.txt", "MINOR", "File Not Found"),
                ("InvalidLines.txt", "MINOR", "Invalid Lines In File"),
            ]
        )
    )
    @skip_if_recsim
    def test_GIVEN_not_using_excitations_OR_invalid_file_WHEN_set_temp_sp_THEN_thresholds_not_recalculated(
        self, _, filename, expected_error_severity, expected_error
    ):
        with self._ioc.start_with_macros(
            {"EXCITATION_THRESHOLD_FILE": filename}, pv_to_wait_for=THRESHOLD_FILE_PV
        ):
            self.ca.assert_that_pv_is_path(THRESHOLD_FILE_PV, THRESHOLD_FILES_DIR + filename)
            for temp_sp, temp, excitation in [
                (5.2, 3.1, "30 nA"),
                (16.4, 18.2, "100 nA"),
                (20.9, 0, "Off"),
                (400.2, 20.3, "1 mV"),
            ]:
                # Reset pv values to test
                self.reset_thresholds_values(
                    excitation, temp, excitation, "No Error", "NO", temp_sp - 10
                )
                # Set temp
                self.ca.assert_setting_setpoint_sets_readback(
                    temp_sp, readback_pv="A:TEMP:SP:RBV", set_point_pv="A:TEMP:SP"
                )
                self._lewis.backdoor_set_on_device("temp_a", temp_sp)
                # Assert nothing has changed
                self.assert_threshold_values(
                    excitation, temp, excitation, expected_error, expected_error_severity, "NO"
                )
