import unittest
from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, skip_if_devsim
from utils.test_modes import TestModes


DEVICE_PREFIX = "NGPSPSU_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("NGPSPSU"),
        "macros": {},
        "emulator": "ngpspsu",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

##############################################
#
#       Useful functions to run tests
#
##############################################


def reset_emulator():
    """Reset the sp2xx device"""
    lewis, ioc = get_running_lewis_and_ioc("ngpspsu", DEVICE_PREFIX)
    ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

    _reset_device(ca)
    _reset_error(ca)
    ca.assert_that_pv_is("ERROR", "")
    ca.assert_that_pv_is("STAT:ON_OFF", "OFF")

    _connect_device(lewis)

    return lewis, ioc, ca


def _stop_device(ca):
    ca.set_pv_value("ON_OFF:SP", 0)


def _start_device(ca):
    ca.set_pv_value("ON_OFF:SP", 1)


def _reset_error(ca):
    ca.set_pv_value("ERROR", "")


def _reset_device(ca):
    ca.process_pv("RESET:SP")


def _connect_device(lewis):
    lewis.backdoor_run_function_on_device("connect")


##############################################
#
#       Unit tests
#
##############################################


class NgpspsuMiscTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def _disconnect_emulator(self):
        self._lewis.backdoor_run_function_on_device("disconnect")

    def test_that_WHEN_the_ioc_is_started_THEN_the_ioc_is_not_disabled(self):
        # When/Then:
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_that_WHEN_requested_THEN_we_get_the_version_and_firmware(self):
        # When:
        self.ca.process_pv("VERSION")

        # Then:
        self.ca.assert_that_pv_is("VERSION", "NGPS 100-50:0.9.01")

    @skip_if_recsim("Recsim is unable to simulate a disconnected device")
    def test_that_GIVEN_a_disconnected_device_WHEN_started_THEN_an_INVALID_alarm_shows(self):
        # Given
        self._disconnect_emulator()

        # When:
        _start_device(self.ca)

        # Then:
        self.ca.assert_that_pv_alarm_is("ON_OFF:SP:RAW", self.ca.Alarms.INVALID)


class NgpspsuStartAndStopTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def test_that_GIVEN_a_fresh_device_THEN_the_device_is_off(self):
        # When/Then:
        self.ca.assert_that_pv_is("STAT:ON_OFF", "OFF")

    @skip_if_recsim("Can't test if the device is turned on")
    def test_that_WHEN_started_THEN_the_device_turns_on(self):
        # When:
        _start_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("STAT:ON_OFF", "ON")

    @skip_if_recsim("Can't test if the device is turned on")
    def test_that_GIVEN_a_device_which_is_running_THEN_the_device_turns_off(self):
        # Given:
        _start_device(self.ca)
        self.ca.assert_that_pv_is("STAT:ON_OFF", "ON")

        # When
        _stop_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("STAT:ON_OFF", "OFF")


class NgpspsuStatusTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def test_that_GIVEN_a_setup_device_THEN_the_status_is_zero(self):
        # When/Then:
        for digit in range(1, 9):
            self.ca.assert_that_pv_is("STAT:HEX:{}".format(digit), 0)


class NgpspsuErrorTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def test_that_GIVEN_a_setup_device_THEN_there_is_no_error_state(self):
        # When/Then:
        self.ca.assert_that_pv_is("ERROR", "")

    @skip_if_recsim("Cannot catch errors in RECSIM")
    def test_that_GIVEN_a_running_device_WHEN_told_to_start_THEN_it_does_not_with_no_error_state(self):
        # Given
        _start_device(self.ca)

        # When
        _start_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("ERROR", "")

    @skip_if_recsim("Cannot catch errors in RECSIM")
    def test_that_GIVEN_a_stopped_device_WHEN_told_to_stop_THEN_it_does_not_with_no_error_state(self):
        # Given
        _stop_device(self.ca)

        # When
        _stop_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("ERROR", "")

    @skip_if_recsim("Can't reset the device in RECSIM.")
    def test_that_GIVEN_device_which_is_off_WHEN_setting_the_voltage_setpoint_THEN_an_error_is_caught(self):
        # Given
        self.ca.assert_that_pv_is("STAT:ON_OFF", "OFF")

        # When
        self.ca.set_pv_value("VOLT:SP", 1.05)

        # Then:
        self.ca.assert_that_pv_is("ERROR", "13")

    @skip_if_recsim("Can't reset the device in RECSIM.")
    def test_that_GIVEN_device_which_is_on_WHEN_RAW_is_turned_on_THEN_an_error_is_caught(self):
        # Given
        _start_device(self.ca)
        self.ca.assert_that_pv_is("STAT:ON_OFF", "ON")

        # When
        self.ca.set_pv_value("ON_OFF:SP:RAW", 1)

        # Then:
        self.ca.assert_that_pv_is("ERROR", "09")

    @skip_if_recsim("Can't reset the device in RECSIM.")
    def test_that_GIVEN_device_which_is_off_WHEN_RAW_is_turned_off_THEN_an_error_is_caught(self):
        # Given
        self.ca.assert_that_pv_is("STAT:ON_OFF", "OFF")

        # When
        self.ca.set_pv_value("ON_OFF:SP:RAW", 0)

        # Then:
        self.ca.assert_that_pv_is("ERROR", "13")


class NgpspsuResetTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    @skip_if_recsim("Can't reset the device in RECSIM.")
    def test_that_GIVEN_a_running_device_WHEN_reset_THEN_the_device_stops(self):
        # Given
        _start_device(self.ca)

        # When
        _reset_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("ERROR", "")

    @skip_if_recsim("Can't reset the device in RECSIM.")
    def test_that_GIVEN_a_running_device_WHEN_reset_THEN_current_is_set_to_zero(self):
        # Given
        _start_device(self.ca)

        # When
        _reset_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("CURR", 0)

    @skip_if_recsim("Can't reset the device in RECSIM.")
    def test_that_GIVEN_a_running_device_WHEN_reset_THEN_voltage_is_set_to_zero(self):
        # Given
        _start_device(self.ca)

        # When
        _reset_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("VOLT", 0)

    @skip_if_recsim("Can't reset the device in RECSIM.")
    def test_that_GIVEN_an_error_WHEN_reset_THEN_the_error_disappears(self):
        # Given
        self.ca.assert_that_pv_is("STAT:ON_OFF", "OFF")
        self.ca.set_pv_value("ON_OFF:SP:RAW", 0)
        self.ca.assert_that_pv_is("ERROR", "13")

        # When:
        _reset_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("ERROR", "")


class NgpspsuVoltageTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def test_that_GIVEN_a_reset_device_THEN_the_voltage_is_zero(self):
        # Given:
        _reset_device(self.ca)

        # When/Then:
        self.ca.assert_that_pv_is("VOLT", 0.0)

    @parameterized.expand([
        ("12.006768", 12.006768),
        ("23", 23),
        ("-5", -5),
        ("-2.78", -2.78),
        ("3e-5", 3e-5),
        ("0.00445676e4", 0.00445676e4),
        ("0", 0)
    ])
    @skip_if_recsim("Can't test if the device is turned on")
    def test_that_GIVEN_device_which_is_on_WHEN_setting_the_voltage_setpoint_THEN_it_is_set(self, _, value):
        # Given:
        _start_device(self.ca)
        self.ca.assert_that_pv_is("STAT:ON_OFF", "ON")

        # When\Then:
        self.ca.assert_setting_setpoint_sets_readback(value, "VOLT:SP:RBV", "VOLT:SP")


class NgpspsuCurrentTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def test_that_GIVEN_a_device_after_set_up_THEN_the_current_is_zero(self):
        # Then:
        self.ca.assert_that_pv_is("CURR", 0.0)

    @parameterized.expand([
        ("12.006768", 12.006768),
        ("23", 23),
        ("-5", -5),
        ("-2.78", -2.78),
        ("3e-5", 3e-5),
        ("0.00445676e4", 0.00445676e4),
        ("0", 0)
    ])
    @skip_if_recsim("Can't test if the device is turned on")
    def test_that_GIVEN_device_which_is_on_WHEN_setting_the_current_setpoint_THEN_it_is_set(self, _, value):
        # Given:
        _start_device(self.ca)
        self.ca.assert_that_pv_is("STAT:ON_OFF", "ON")

        # When\Then:
        self.ca.assert_setting_setpoint_sets_readback(value, "CURR:SP:RBV", "CURR:SP")


class NgpspsuRecsimOnlyVoltageAndCurrentTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def _set_voltage_setpoint(self, value):
        self._ioc.set_simulated_value("SIM:VOLT:SP", value)

    def _set_current_setpoint(self, value):
        self._ioc.set_simulated_value("SIM:CURR:SP", value)

    @parameterized.expand([
        ("12.006768", 12.006768),
        ("23", 23),
        ("-5", -5),
        ("-2.78", -2.78),
        ("3e-5", 3e-5),
        ("0.00445676e4", 0.00445676e4),
        ("0", 0)
    ])
    @skip_if_devsim("These tests will fail in devsim as the device is not on.")
    def test_that_WHEN_setting_the_current_setpoint_THEN_it_is_set(self, _, value):
        # When
        self._set_current_setpoint(value)

        # Then:
        self.ca.assert_that_pv_is("CURR:SP:RBV", value)

    @parameterized.expand([
        ("12.006768", 12.006768),
        ("23", 23),
        ("-5", -5),
        ("-2.78", -2.78),
        ("3e-5", 3e-5),
        ("0.00445676e4", 0.00445676e4),
        ("0", 0)
    ])
    @skip_if_devsim("These tests will fail in devsim as the device is not on.")
    def test_that_WHEN_setting_the_voltage_setpoint_THEN_it_is_set(self, _, value):
        # When
        self._set_voltage_setpoint(value)

        # Then:
        self.ca.assert_that_pv_is("VOLT:SP:RBV", value)


class NgpspsuFaultTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    @skip_if_recsim("Can't see faults from the status")
    def test_that_GIVEN_a_reset_device_THEN_the_fault_pv_is_not_in_alarm(self):
        # Given:
        _reset_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("STAT:FAULT", "No fault")
        self.ca.assert_that_pv_alarm_is("STAT:FAULT", self.ca.Alarms.NONE)

    @parameterized.expand([
        ("fault_condition", "fault_condition"),
        ("mains_fault", "mains_fault"),
        ("earth_leakage_fault", "earth_leakage_fault"),
        ("earth_fuse_fault", "earth_fuse_fault"),
        ("regulation_fault", "regulation_fault"),
        ("dcct_fault", "dcct_fault")
    ])
    @skip_if_recsim("Can't see faults from the status")
    def test_that_GIVEN_a_device_experiencing_a_fault_THEN_the_fault_pv_is_in_alarm(self, _, fault_name):
        # Given:
        self._lewis.backdoor_run_function_on_device("fault", [fault_name])

        # Then:
        self.ca.assert_that_pv_is("STAT:FAULT", "Fault")
        self.ca.assert_that_pv_alarm_is("STAT:FAULT", self.ca.Alarms.MAJOR)
