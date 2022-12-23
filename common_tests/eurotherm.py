import abc
import os
import unittest

from parameterized import parameterized

import time
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim
from utils.ioc_launcher import IOCRegister, EPICS_TOP
from utils.calibration_utils import reset_calibration_file, use_calibration_file

SENSOR_DISCONNECTED_VALUE = 1529
NONE_TXT_CALIBRATION_MAX_TEMPERATURE = 10000.0
NONE_TXT_CALIBRATION_MIN_TEMPERATURE = 0.0

# PV names
RBV_PV = "RBV"

TEST_VALUES = [-50, 0.1, 50, 3000]

# PIDs cannot be floating-point
PID_TEST_VALUES = [-50, 50, 3000]


class EurothermBaseTests(metaclass=abc.ABCMeta):
    """
    Tests for the Eurotherm temperature controller.
    """
    @abc.abstractmethod
    def get_device(self):
        pass

    @abc.abstractmethod
    def get_emulator_device(self):
        pass

    def get_prefix(self):
        return "{}:A01".format(self.get_device())

    def setUp(self):
        self._setup_lewis_and_channel_access()
        self._reset_device_state()

    def _setup_lewis_and_channel_access(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(self.get_emulator_device(), self.get_device())
        self.ca = ChannelAccess(device_prefix=self.get_prefix(), default_wait_time=0)
        self.ca.assert_that_pv_exists(RBV_PV, timeout=30)
        self.ca.assert_that_pv_exists("CAL:SEL", timeout=10)

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
        tolerance = 0.2
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

    def test_GIVEN_temperature_set_WHEN_changing_calibration_files_THEN_temperature_rb_pvs_update(self):
        temperature = 50
        temperature_calibrated = 500
        tolerance = 1
        self._set_setpoint_and_current_temperature(temperature)
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt"):
            self.ca.assert_that_pv_is_number("TEMP", temperature, tolerance=tolerance)
            self.ca.assert_that_pv_is_number("TEMP:SP:RBV", temperature, tolerance=tolerance)

        with use_calibration_file(self.ca, "C.txt"):
            self.ca.assert_that_pv_is_number("TEMP", temperature_calibrated, tolerance=tolerance)
            self.ca.assert_that_pv_is_number("TEMP:SP:RBV", temperature_calibrated, tolerance=tolerance)

        with use_calibration_file(self.ca, "None.txt"):
            self.ca.assert_that_pv_is_number("TEMP", temperature, tolerance=tolerance)
            self.ca.assert_that_pv_is_number("TEMP:SP:RBV", temperature, tolerance=tolerance)

    def _assert_units(self, units):
        # High timeouts because setting units does not cause processing - wait for normal scan loop to come around.
        self.ca.assert_that_pv_is("TEMP.EGU", units, timeout=30)
        self.ca.assert_that_pv_is("TEMP:SP.EGU", units, timeout=30)
        self.ca.assert_that_pv_is("TEMP:SP:RBV.EGU", units, timeout=30)

    def _assert_using_mock_table_location(self):
        for pv in ["TEMP", "TEMP:SP:CONV", "TEMP:SP:RBV:CONV"]:
            self.ca.assert_that_pv_is("{}.TDIR".format(pv), r"eurotherm2k/master/example_temp_sensor")
            self.ca.assert_that_pv_is_path("{}.BDIR".format(pv), os.path.join(EPICS_TOP, "support").replace("\\", "/"))

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

    @parameterized.expand(["TEMP", "TEMP:SP:RBV", "P", "I", "D", "AUTOTUNE", "MAX_OUTPUT", "LOWLIM"])
    def test_WHEN_disconnected_THEN_in_alarm(self, record):
        self.ca.assert_that_pv_alarm_is(record, ChannelAccess.Alarms.NONE)
        with self._lewis.backdoor_simulate_disconnected_device():
            self.ca.assert_that_pv_alarm_is(record, ChannelAccess.Alarms.INVALID, timeout=30)
        # Assert alarms clear on reconnection
        self.ca.assert_that_pv_alarm_is(record, ChannelAccess.Alarms.NONE, timeout=30)

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_p_set_via_backdoor_THEN_p_updates(self, _, val):
        self._lewis.backdoor_set_on_device("p", val)
        self.ca.assert_that_pv_is_number("P", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_i_set_via_backdoor_THEN_i_updates(self, _, val):
        self._lewis.backdoor_set_on_device("i", val)
        self.ca.assert_that_pv_is_number("I", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_d_set_via_backdoor_THEN_d_updates(self, _, val):
        self._lewis.backdoor_set_on_device("d", val)
        self.ca.assert_that_pv_is_number("D", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list(TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_output_set_via_backdoor_THEN_output_updates(self, _, val):
        self._lewis.backdoor_set_on_device("output", val)
        self.ca.assert_that_pv_is_number("OUTPUT", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list(TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_output_set_via_backdoor_THEN_output_updates(self, _, val):
        self._lewis.backdoor_set_on_device("max_output", val)
        self.ca.assert_that_pv_is_number("MAX_OUTPUT", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list([0, 100, 9999]))
    def test_WHEN_output_rate_set_THEN_output_rate_updates(self, _, val):
        self.ca.assert_setting_setpoint_sets_readback(value=val, readback_pv="OUTPUT_RATE", timeout=15)

    @parameterized.expand(parameterized_list(TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_high_limit_set_via_backdoor_THEN_high_lim_updates(self, _, val):
        self._lewis.backdoor_set_on_device("high_lim", val)
        self.ca.assert_that_pv_is_number("HILIM", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list(TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_low_limit_set_via_backdoor_THEN_low_lim_updates(self, _, val):
        self._lewis.backdoor_set_on_device("low_lim", val)
        self.ca.assert_that_pv_is_number("LOWLIM", val, tolerance=0.05, timeout=15)
