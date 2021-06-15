import os
import unittest
from parameterized import parameterized

import time
from utils.channel_access import ChannelAccess
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister, EPICS_TOP
from utils.calibration_utils import reset_calibration_file, use_calibration_file

# Internal Address of device (must be 2 characters)
ADDRESS = "A01"
# Numerical address of the device
ADDR_1 = 1
DEVICE = "EUROTHRM_01"
PREFIX = "{}:{}".format(DEVICE, ADDRESS)

# PV names
RBV_PV = "RBV"

EMULATOR_DEVICE = "eurotherm"

IOCS = [
    {
        "name": DEVICE,
        "directory": get_default_ioc_dir("EUROTHRM"),
        "macros": {
            "ADDR": ADDRESS,
            "ADDR_1": ADDR_1,
            "ADDR_2": "",
            "ADDR_3": "",
            "ADDR_4": "",
            "ADDR_5": "",
            "ADDR_6": "",
            "ADDR_7": "",
            "ADDR_8": ""
        },
        "emulator": EMULATOR_DEVICE,
    },
]

SENSOR_DISCONNECTED_VALUE = 1529
NONE_TXT_CALIBRATION_MAX_TEMPERATURE = 10000.0
NONE_TXT_CALIBRATION_MIN_TEMPERATURE = 0.0


TEST_MODES = [TestModes.DEVSIM]


class EurothermTests(unittest.TestCase):
    """
    Tests for the Eurotherm temperature controller.
    """

    def setUp(self):
        self._setup_lewis_and_channel_access()
        self._reset_device_state()

    def _setup_lewis_and_channel_access(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_DEVICE, DEVICE)
        self.ca = ChannelAccess(device_prefix=PREFIX)
        self.ca.assert_that_pv_exists(RBV_PV, timeout=30)
        self.ca.assert_that_pv_exists("CAL:SEL", timeout=10)
        self._lewis.backdoor_set_on_device("address", ADDRESS)

    def _reset_device_state(self):
        self._lewis.backdoor_set_on_device('connected', True)
        reset_calibration_file(self.ca)

        intial_temp = 0.0

        self._set_setpoint_and_current_temperature(intial_temp)

        self._lewis.backdoor_set_on_device("ramping_on", False)
        self._lewis.backdoor_set_on_device("ramp_rate", 1.0)
        self.ca.set_pv_value("RAMPON:SP", 0, sleep_after_set=0)

        self._set_setpoint_and_current_temperature(intial_temp)
        self.ca.assert_that_pv_is("TEMP", intial_temp)
        # Ensure the temperature isn't being changed by a ramp any more
        self.ca.assert_that_pv_value_is_unchanged("TEMP", 5)

    def _set_setpoint_and_current_temperature(self, temperature):
        if IOCRegister.uses_rec_sim:
            self.ca.set_pv_value("SIM:TEMP:SP", temperature)
            self.ca.assert_that_pv_is("SIM:TEMP", temperature)
            self.ca.assert_that_pv_is("SIM:TEMP:SP", temperature)
            self.ca.assert_that_pv_is("SIM:TEMP:SP:RBV", temperature)
        else:
            self._lewis.backdoor_set_on_device("current_temperature", temperature)
            self.ca.assert_that_pv_is_number("TEMP", temperature, 0.1)
            self._lewis.backdoor_set_on_device("ramp_setpoint_temperature", temperature)
            self.ca.assert_that_pv_is_number("TEMP:SP:RBV", temperature, 0.1)

    def test_WHEN_read_rbv_temperature_THEN_rbv_value_is_same_as_backdoor(self):
        expected_temperature = 10.0
        self._set_setpoint_and_current_temperature(expected_temperature)
        self.ca.assert_that_pv_is(RBV_PV, expected_temperature)

    def test_GIVEN_a_sp_WHEN_sp_read_rbv_temperature_THEN_rbv_value_is_same_as_sp(self):
        expected_temperature = 10.0
        self.ca.assert_setting_setpoint_sets_readback(expected_temperature, "SP:RBV", "SP")

    def test_WHEN_set_ramp_rate_in_K_per_min_THEN_current_temperature_reaches_set_point_in_expected_time(self):
        start_temperature = 5.0
        ramp_on = 1
        ramp_rate = 60.0
        setpoint_temperature = 25.0

        self._set_setpoint_and_current_temperature(start_temperature)

        self.ca.set_pv_value("RATE:SP", ramp_rate)
        self.ca.assert_that_pv_is_number("RATE", ramp_rate, 0.1)
        self.ca.set_pv_value("RAMPON:SP", ramp_on)
        self.ca.set_pv_value("TEMP:SP", setpoint_temperature)

        start = time.time()
        self.ca.assert_that_pv_is_number("TEMP:SP:RBV", setpoint_temperature, tolerance=0.1, timeout=60)
        end = time.time()
        self.assertAlmostEquals(end-start, 60. * (setpoint_temperature-start_temperature)/ramp_rate,
                                delta=0.1*(end-start))  # Tolerance of 10%. Tolerance of 1s is too tight given scan rate

    def test_WHEN_sensor_disconnected_THEN_ramp_setting_is_disabled(self):
        self._lewis.backdoor_set_on_device("current_temperature", SENSOR_DISCONNECTED_VALUE)

        self.ca.assert_that_pv_is_number("RAMPON:SP.DISP", 1)

    def test_GIVEN_sensor_disconnected_WHEN_sensor_reconnected_THEN_ramp_setting_is_enabled(self):
        self._lewis.backdoor_set_on_device("current_temperature", SENSOR_DISCONNECTED_VALUE)

        self._lewis.backdoor_set_on_device("current_temperature", 0)

        self.ca.assert_that_pv_is_number("RAMPON:SP.DISP", 0)

    def test_GIVEN_ramp_was_off_WHEN_sensor_disconnected_THEN_ramp_is_off_and_cached_ramp_value_is_off(self):
        self.ca.set_pv_value("RAMPON:SP", 0)

        self._lewis.backdoor_set_on_device("current_temperature", SENSOR_DISCONNECTED_VALUE)

        self.ca.assert_that_pv_is("RAMPON", "OFF")
        self.ca.assert_that_pv_is("RAMPON:CACHE", "OFF")

    def test_GIVEN_ramp_was_on_WHEN_sensor_disconnected_THEN_ramp_is_off_and_cached_ramp_value_is_on(self):
        self.ca.set_pv_value("RAMPON:SP", 1)

        self._lewis.backdoor_set_on_device("current_temperature", SENSOR_DISCONNECTED_VALUE)

        self.ca.assert_that_pv_is("RAMPON", "OFF")
        self.ca.assert_that_pv_is("RAMPON:CACHE", "ON")

    def test_GIVEN_ramp_was_on_WHEN_sensor_disconnected_and_reconnected_THEN_ramp_is_on(self):
        self.ca.set_pv_value("RAMPON:SP", 1)

        self._lewis.backdoor_set_on_device("current_temperature", SENSOR_DISCONNECTED_VALUE)
        self.ca.assert_that_pv_is("RAMPON", "OFF")
        self._lewis.backdoor_set_on_device("current_temperature", 0)

        self.ca.assert_that_pv_is("RAMPON", "ON")

    def test_GIVEN_temperature_setpoint_followed_by_calibration_change_WHEN_same_setpoint_set_again_THEN_setpoint_readback_updates_to_set_value(self):
        # Arrange
        temperature = 50.0
        rbv_change_timeout = 10
        tolerance = 0.01
        self.ca.set_pv_value("RAMPON:SP", 0)
        reset_calibration_file(self.ca)
        self.ca.set_pv_value("TEMP:SP", temperature)
        self.ca.assert_that_pv_is_number("TEMP:SP:RBV", temperature, tolerance=tolerance, timeout=rbv_change_timeout)
        with use_calibration_file(self.ca, "C006.txt"):
            self.ca.assert_that_pv_is_not_number("TEMP:SP:RBV", temperature, tolerance=tolerance, timeout=rbv_change_timeout)

            # Act
            self.ca.set_pv_value("TEMP:SP", temperature)

            # Assert
            self.ca.assert_that_pv_is_number("TEMP:SP:RBV", temperature, tolerance=tolerance, timeout=rbv_change_timeout)

    def _assert_units(self, units):
        # High timeouts because setting units does not cause processing - wait for normal scan loop to come around.
        self.ca.assert_that_pv_is("TEMP.EGU", units, timeout=30)
        self.ca.assert_that_pv_is("TEMP:SP.EGU", units, timeout=30)
        self.ca.assert_that_pv_is("TEMP:SP:RBV.EGU", units, timeout=30)

    def _assert_using_mock_table_location(self):
        for pv in ["TEMP", "TEMP:SP:CONV", "TEMP:SP:RBV:CONV"]:
            self.ca.assert_that_pv_is("{}.TDIR".format(pv), r"eurotherm2k/master/example_temp_sensor")
            self.ca.assert_that_pv_is("{}.BDIR".format(pv), EPICS_TOP.replace("\\", "/") + "support")

    def test_WHEN_calibration_file_is_in_units_of_K_THEN_egu_of_temperature_pvs_is_K(self):
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "K.txt"):
            self._assert_units("K")

    def test_WHEN_calibration_file_is_in_units_of_C_THEN_egu_of_temperature_pvs_is_C(self):
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "C.txt"):
            self._assert_units("C")

    def test_WHEN_calibration_file_has_no_units_THEN_egu_of_temperature_pvs_is_K(self):
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt"):
            self._assert_units("K")

    def test_WHEN_config_file_and_temperature_unit_changed_THEN_then_ramp_rate_unit_changes(self):
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt"):
            self._assert_units("K")
            self.ca.assert_that_pv_is("RATE.EGU", "K/min")

        with use_calibration_file(self.ca, "C.txt"):
            self._assert_units("C")
            self.ca.assert_that_pv_is("RATE.EGU", "C/min")

    @parameterized.expand([
        ("under_range_calc_pv_is_under_range",  NONE_TXT_CALIBRATION_MIN_TEMPERATURE - 5.0, 1.0),
        ("under_range_calc_pv_is_within_range", NONE_TXT_CALIBRATION_MIN_TEMPERATURE + 200, 0.0),
        ("under_range_calc_pv_is_within_range", NONE_TXT_CALIBRATION_MIN_TEMPERATURE, 0.0)
    ])
    def test_GIVEN_None_txt_calibration_file_WHEN_temperature_is_set_THEN(
            self, _, temperature, expected_value_of_under_range_calc_pv):
        # Arrange

        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt"):
            self.ca.assert_that_pv_exists("CAL:RANGE")
            self.ca.assert_that_pv_is("TEMP:RANGE:UNDER.B", NONE_TXT_CALIBRATION_MIN_TEMPERATURE)

            # Act:
            self._set_setpoint_and_current_temperature(temperature)

            # Assert

            self.ca.assert_that_pv_is("TEMP:RANGE:UNDER.A", temperature)
            self.ca.assert_that_pv_is("TEMP:RANGE:UNDER", expected_value_of_under_range_calc_pv)

    @parameterized.expand([
        ("over_range_calc_pv_is_over_range", NONE_TXT_CALIBRATION_MAX_TEMPERATURE + 5.0, 1.0),
        ("over_range_calc_pv_is_within_range", NONE_TXT_CALIBRATION_MAX_TEMPERATURE - 200, 0.0),
        ("over_range_calc_pv_is_within_range", NONE_TXT_CALIBRATION_MAX_TEMPERATURE, 0.0)
    ])
    def test_GIVEN_None_txt_calibration_file_WHEN_temperature_is_set_THEN(
            self, _, temperature, expected_value_of_over_range_calc_pv):
        # Arrange

        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt"):
            self.ca.assert_that_pv_exists("CAL:RANGE")
            self.ca.assert_that_pv_is("TEMP:RANGE:OVER.B", NONE_TXT_CALIBRATION_MAX_TEMPERATURE)

            # Act:
            self._set_setpoint_and_current_temperature(temperature)

            # Assert
            self.ca.assert_that_pv_is("TEMP:RANGE:OVER.A", temperature)
            self.ca.assert_that_pv_is("TEMP:RANGE:OVER", expected_value_of_over_range_calc_pv)

    def test_GIVEN_None_txt_calibration_file_WHEN_changed_to_C006_txt_calibration_file_THEN_the_calibration_limits_change(
            self):
        C006_CALIBRATION_FILE_MAX = 330.26135292267900000000
        C006_CALIBRATION_FILE_MIN = 1.20927230303971000000

        # Arrange
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt"):
            self.ca.assert_that_pv_exists("CAL:RANGE")
            self.ca.assert_that_pv_is("TEMP:RANGE:OVER.B", NONE_TXT_CALIBRATION_MAX_TEMPERATURE)
            self.ca.assert_that_pv_is("TEMP:RANGE:UNDER.B", NONE_TXT_CALIBRATION_MIN_TEMPERATURE)

        # Act:
        with use_calibration_file(self.ca, "C006.txt"):

            # Assert
            self.ca.assert_that_pv_is("TEMP:RANGE:OVER.B", C006_CALIBRATION_FILE_MAX)
            self.ca.assert_that_pv_is("TEMP:RANGE:UNDER.B", C006_CALIBRATION_FILE_MIN)

    @parameterized.expand(["TEMP", "TEMP:SP:RBV", "P", "I", "D", "AUTOTUNE", "MAX_OUTPUT", "LOWLIM"])
    def test_WHEN_disconnected_THEN_in_alarm(self, record):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is(record, ChannelAccess.Alarms.INVALID)
