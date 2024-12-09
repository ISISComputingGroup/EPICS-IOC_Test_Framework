import abc
import os
import time
import typing
import unittest
from typing import ContextManager

from parameterized import parameterized

from utils.calibration_utils import reset_calibration_file, use_calibration_file
from utils.channel_access import ChannelAccess
from utils.emulator_launcher import LewisLauncher
from utils.ioc_launcher import EPICS_TOP, IOCRegister
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim

SENSOR_DISCONNECTED_VALUE = 1529
NONE_TXT_CALIBRATION_MAX_TEMPERATURE = 10000.0
NONE_TXT_CALIBRATION_MIN_TEMPERATURE = 0.0
SCALING = "1.0"

TEST_VALUES = [-50, 0.1, 50, 3000]

# PIDs cannot be floating-point
PID_TEST_VALUES = [-50, 50, 3000]

SENSORS = ["01", "02", "03", "04", "05", "06"]

PV_SENSORS = ["A01", "A02", "A03", "A04", "A05", "A06"]


# This class is only valid for classes which also derive from unittest.TestCase,
# and we can't derive from unittest.TestCase at runtime, because
# unittest would try to execute them as tests
class EurothermBaseTests(
    unittest.TestCase if typing.TYPE_CHECKING else object, metaclass=abc.ABCMeta
):
    """
    Tests for the Eurotherm temperature controller.
    """

    @abc.abstractmethod
    def get_device(self) -> str:
        pass

    @abc.abstractmethod
    def get_emulator_device(self) -> str:
        pass

    @abc.abstractmethod
    def _get_temperature_setter_wrapper(self) -> ContextManager:
        pass

    @abc.abstractmethod
    def get_scaling(self) -> str:
        pass

    def get_prefix(self) -> str:
        return "{}:A01".format(self.get_device())

    def setUp(self):
        self._setup_lewis_and_channel_access()
        self._reset_device_state()
        self.ca_no_prefix = ChannelAccess()
        self._lewis: LewisLauncher

    def _setup_lewis_and_channel_access(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("eurotherm", "EUROTHRM_01")  # type:ignore
        self.ca = ChannelAccess(device_prefix="EUROTHRM_01", default_wait_time=0)
        self.ca.assert_that_pv_exists("A01:RBV", timeout=30)
        self.ca.assert_that_pv_exists("A01:CAL:SEL", timeout=10)

    def _reset_device_state(self, sensor=PV_SENSORS[0]):
        i = PV_SENSORS.index(sensor)
        self._lewis.backdoor_run_function_on_device("set_connected", [SENSORS[i], True])
        reset_calibration_file(self.ca, prefix=f"{sensor}:")

        intial_temp = 0.0

        self._set_setpoint_and_current_temperature(intial_temp)

        self._lewis.backdoor_run_function_on_device("set_ramping_on", [SENSORS[0], True])
        self._lewis.backdoor_run_function_on_device("set_ramp_rate", [SENSORS[0], 1.0])
        self.ca.set_pv_value(f"{sensor}:RAMPON:SP", 0, sleep_after_set=0)

        self._set_setpoint_and_current_temperature(intial_temp)
        self.ca.assert_that_pv_is(f"{sensor}:TEMP", intial_temp)
        # Ensure the temperature isn't being changed by a ramp any more
        self.ca.assert_that_pv_value_is_unchanged(f"{sensor}:TEMP", wait=3)

    def _set_setpoint_and_current_temperature(self, temperature, sensor=PV_SENSORS[0]):
        if IOCRegister.uses_rec_sim:
            self.ca.set_pv_value(f"{sensor}:SIM:TEMP:SP", temperature)
            self.ca.assert_that_pv_is(f"{sensor}:SIM:TEMP", temperature)
            self.ca.assert_that_pv_is(f"{sensor}:SIM:TEMP:SP", temperature)
            self.ca.assert_that_pv_is(f"{sensor}:SIM:TEMP:SP:RBV", temperature)
        else:
            i = PV_SENSORS.index(sensor)
            self._lewis.backdoor_run_function_on_device(
                "set_current_temperature", [SENSORS[i], temperature]
            )
            self.ca.assert_that_pv_is_number(f"{sensor}:TEMP", temperature, 0.1, timeout=30)
            self._lewis.backdoor_run_function_on_device(
                "set_ramp_setpoint_temperature", [SENSORS[i], temperature]
            )
            self.ca.assert_that_pv_is_number(f"{sensor}:TEMP:SP:RBV", temperature, 0.1, timeout=30)

    def test_WHEN_read_rbv_temperature_THEN_rbv_value_is_same_as_backdoor(self):
        expected_temperature = 10.0
        self._set_setpoint_and_current_temperature(expected_temperature)
        self.ca.assert_that_pv_is("A01:RBV", expected_temperature)

    def test_GIVEN_a_sp_WHEN_sp_read_rbv_temperature_THEN_rbv_value_is_same_as_sp(self):
        expected_temperature = 10.0
        self.ca.assert_setting_setpoint_sets_readback(expected_temperature, "A01:SP:RBV", "A01:SP")

    def test_WHEN_set_ramp_rate_in_K_per_min_THEN_current_temperature_reaches_set_point_in_expected_time(
        self,
    ):
        start_temperature = 5.0
        ramp_on = 1
        ramp_rate = 60.0
        setpoint_temperature = 25.0

        self._set_setpoint_and_current_temperature(start_temperature)

        self.ca.set_pv_value("A01:RATE:SP", ramp_rate)
        self.ca.assert_that_pv_is_number("A01:RATE", ramp_rate, 0.1)
        self.ca.set_pv_value("A01:RAMPON:SP", ramp_on)
        with self._get_temperature_setter_wrapper():
            self.ca.set_pv_value("A01:TEMP:SP", setpoint_temperature)

        start = time.time()
        self.ca.assert_that_pv_is_number(
            "A01:TEMP:SP:RBV", setpoint_temperature, tolerance=0.1, timeout=60
        )
        end = time.time()
        self.assertAlmostEqual(
            end - start,
            60.0 * (setpoint_temperature - start_temperature) / ramp_rate,
            delta=0.1 * (end - start),
        )  # Lower tolerance will be too tight given scan rate

    def test_WHEN_sensor_disconnected_THEN_ramp_setting_is_disabled(self):
        self._lewis.backdoor_run_function_on_device(
            "set_current_temperature", [SENSORS[0], SENSOR_DISCONNECTED_VALUE]
        )

        self.ca.assert_that_pv_is_number("A01:RAMPON:SP.DISP", 1)

    def test_GIVEN_sensor_disconnected_WHEN_sensor_reconnected_THEN_ramp_setting_is_enabled(self):
        self._lewis.backdoor_run_function_on_device(
            "set_current_temperature", [SENSORS[0], SENSOR_DISCONNECTED_VALUE]
        )

        self._lewis.backdoor_run_function_on_device("set_current_temperature", [SENSORS[0], 0])

        self.ca.assert_that_pv_is_number("A01:RAMPON:SP.DISP", 0)

    def test_GIVEN_ramp_was_off_WHEN_sensor_disconnected_THEN_ramp_is_off_and_cached_ramp_value_is_off(
        self,
    ):
        self.ca.set_pv_value("A01:RAMPON:SP", 0)

        self._lewis.backdoor_run_function_on_device(
            "set_current_temperature", [SENSORS[0], SENSOR_DISCONNECTED_VALUE]
        )

        self.ca.assert_that_pv_is("A01:RAMPON", "OFF")
        self.ca.assert_that_pv_is("A01:RAMPON:CACHE", "OFF")

    def test_GIVEN_ramp_was_on_WHEN_sensor_disconnected_THEN_ramp_is_off_and_cached_ramp_value_is_on(
        self,
    ):
        self.ca.set_pv_value("A01:RAMPON:SP", 1)

        self._lewis.backdoor_run_function_on_device(
            "set_current_temperature", [SENSORS[0], SENSOR_DISCONNECTED_VALUE]
        )

        self.ca.assert_that_pv_is("A01:RAMPON", "OFF")
        self.ca.assert_that_pv_is("A01:RAMPON:CACHE", "ON")

    def test_GIVEN_ramp_was_on_WHEN_sensor_disconnected_and_reconnected_THEN_ramp_is_on(self):
        self.ca.set_pv_value("A01:RAMPON:SP", 1)

        self._lewis.backdoor_run_function_on_device(
            "set_current_temperature", [SENSORS[0], SENSOR_DISCONNECTED_VALUE]
        )
        self.ca.assert_that_pv_is("A01:RAMPON", "OFF")
        self._lewis.backdoor_run_function_on_device("set_current_temperature", [SENSORS[0], 0])

        self.ca.assert_that_pv_is("A01:RAMPON", "ON")

    def test_GIVEN_temperature_setpoint_followed_by_calibration_change_WHEN_same_setpoint_set_again_THEN_setpoint_readback_updates_to_set_value(
        self,
    ):
        # Arrange
        temperature = 50.0
        rbv_change_timeout = 10
        tolerance = 0.2
        self.ca.set_pv_value("A01:RAMPON:SP", 0)
        reset_calibration_file(self.ca, prefix="A01:")
        with self._get_temperature_setter_wrapper():
            self.ca.set_pv_value("A01:TEMP:SP", temperature)
        self.ca.assert_that_pv_is_number(
            "A01:TEMP:SP:RBV", temperature, tolerance=tolerance, timeout=rbv_change_timeout
        )
        with use_calibration_file(self.ca, "C006.txt", prefix="A01:"):
            self.ca.assert_that_pv_is_not_number(
                "A01:TEMP:SP:RBV", temperature, tolerance=tolerance, timeout=rbv_change_timeout
            )

            # Act
            with self._get_temperature_setter_wrapper():
                self.ca.set_pv_value("A01:TEMP:SP", temperature)

            # Assert
            self.ca.assert_that_pv_is_number(
                "A01:TEMP:SP:RBV", temperature, tolerance=tolerance, timeout=rbv_change_timeout
            )

    def test_GIVEN_temperature_set_WHEN_changing_calibration_files_THEN_temperature_rb_pvs_update(
        self,
    ):
        temperature = 50
        temperature_calibrated = 500
        tolerance = 1
        self._set_setpoint_and_current_temperature(temperature)
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt", prefix="A01:"):
            self.ca.assert_that_pv_is_number("A01:TEMP", temperature, tolerance=tolerance)
            self.ca.assert_that_pv_is_number("A01:TEMP:SP:RBV", temperature, tolerance=tolerance)

        with use_calibration_file(self.ca, "C.txt", prefix="A01:"):
            self.ca.assert_that_pv_is_number(
                "A01:TEMP", temperature_calibrated, tolerance=tolerance
            )
            self.ca.assert_that_pv_is_number(
                "A01:TEMP:SP:RBV", temperature_calibrated, tolerance=tolerance
            )

        with use_calibration_file(self.ca, "None.txt", prefix="A01:"):
            self.ca.assert_that_pv_is_number("A01:TEMP", temperature, tolerance=tolerance)
            self.ca.assert_that_pv_is_number("A01:TEMP:SP:RBV", temperature, tolerance=tolerance)

    def _assert_units(self, units):
        # High timeouts because setting units does not cause processing - wait for normal scan loop to come around.
        self.ca.assert_that_pv_is("A01:TEMP.EGU", units, timeout=30)
        self.ca.assert_that_pv_is("A01:TEMP:SP.EGU", units, timeout=30)
        self.ca.assert_that_pv_is("A01:TEMP:SP:RBV.EGU", units, timeout=30)

    def _assert_using_mock_table_location(self):
        for pv in ["A01:TEMP", "A01:TEMP:SP:CONV", "A01:TEMP:SP:RBV:CONV"]:
            self.ca.assert_that_pv_is(
                "{}.TDIR".format(pv), r"eurotherm2k/master/example_temp_sensor"
            )
            self.ca.assert_that_pv_is_path(
                "{}.BDIR".format(pv), os.path.join(EPICS_TOP, "support").replace("\\", "/")
            )

    def test_WHEN_calibration_file_is_in_units_of_K_THEN_egu_of_temperature_pvs_is_K(self):
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "K.txt", prefix="A01:"):
            self._assert_units("K")

    def test_WHEN_calibration_file_is_in_units_of_C_THEN_egu_of_temperature_pvs_is_C(self):
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "C.txt", prefix="A01:"):
            self._assert_units("C")

    def test_WHEN_calibration_file_has_no_units_THEN_egu_of_temperature_pvs_is_K(self):
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt", prefix="A01:"):
            self._assert_units("K")

    def test_WHEN_config_file_and_temperature_unit_changed_THEN_then_ramp_rate_unit_changes(self):
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt", prefix="A01:"):
            self._assert_units("K")
            self.ca.assert_that_pv_is("A01:RATE.EGU", "K/min")

        with use_calibration_file(self.ca, "C.txt", prefix="A01:"):
            self._assert_units("C")
            self.ca.assert_that_pv_is("A01:RATE.EGU", "C/min")

    @parameterized.expand(
        [
            ("under_range_calc_pv_is_under_range", NONE_TXT_CALIBRATION_MIN_TEMPERATURE - 5.0, 1.0),
            (
                "under_range_calc_pv_is_within_range",
                NONE_TXT_CALIBRATION_MIN_TEMPERATURE + 200,
                0.0,
            ),
            ("under_range_calc_pv_is_within_range", NONE_TXT_CALIBRATION_MIN_TEMPERATURE, 0.0),
        ]
    )
    def test_GIVEN_None_txt_calibration_file_WHEN_temperature_is_set_THEN(
        self, _, temperature, exp_val
    ):
        # Arrange

        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt", prefix="A01:"):
            self.ca.assert_that_pv_exists("A01:CAL:RANGE")
            self.ca.assert_that_pv_is(
                "A01:TEMP:RANGE:UNDER.B", NONE_TXT_CALIBRATION_MIN_TEMPERATURE
            )

            # Act:
            self._set_setpoint_and_current_temperature(temperature)

            # Assert

            self.ca.assert_that_pv_is("A01:TEMP:RANGE:UNDER.A", temperature)
            self.ca.assert_that_pv_is("A01:TEMP:RANGE:UNDER", expected_value=exp_val)

    def test_WHEN_disconnected_THEN_in_alarm(self):
        records = [
            "A01:TEMP",
            "A01:TEMP:SP:RBV",
            "A01:P",
            "A01:I",
            "A01:D",
            "A01:AUTOTUNE",
            "A01:MAX_OUTPUT",
            "A01:LOWLIM",
        ]
        for record in records:
            self.ca.assert_that_pv_alarm_is(record, ChannelAccess.Alarms.NONE)
        with self._lewis.backdoor_simulate_disconnected_addr():
            for record in records:
                self.ca.assert_that_pv_alarm_is(record, ChannelAccess.Alarms.INVALID, timeout=60)
        # Assert alarms clear on reconnection
        with self._get_temperature_setter_wrapper():
            for record in records:
                self.ca.assert_that_pv_alarm_is(record, ChannelAccess.Alarms.NONE, timeout=30)

    def test_WHEN_eurotherm_missing_THEN_updates_of_PVs_stop(self):
        with self._lewis.backdoor_simulate_disconnected_addr():
            self.ca.assert_that_pv_value_is_unchanged("A01:RBV", 20)

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_p_set_via_backdoor_THEN_p_updates(self, _, val):
        self._lewis.backdoor_run_function_on_device("set_p", [SENSORS[0], val])
        self.ca.assert_that_pv_is_number("A01:P", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_i_set_via_backdoor_THEN_i_updates(self, _, val):
        self._lewis.backdoor_run_function_on_device("set_i", [SENSORS[0], val])
        self.ca.assert_that_pv_is_number("A01:I", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_d_set_via_backdoor_THEN_d_updates(self, _, val):
        self._lewis.backdoor_run_function_on_device("set_d", [SENSORS[0], val])
        self.ca.assert_that_pv_is_number("A01:D", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list(TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_output_set_via_backdoor_THEN_output_updates(self, _, val):
        self._lewis.backdoor_run_function_on_device("set_output", [SENSORS[0], val])
        self.ca.assert_that_pv_is_number("A01:OUTPUT", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list(TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_max_output_set_via_backdoor_THEN_output_updates(self, _, val):
        self._lewis.backdoor_run_function_on_device("set_max_output", [SENSORS[0], val])
        self.ca.assert_that_pv_is_number("A01:MAX_OUTPUT", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list([0, 100, 3276]))
    def test_WHEN_output_rate_set_THEN_output_rate_updates(self, _, val):
        self.ca.assert_setting_setpoint_sets_readback(
            value=val, readback_pv="A01:OUTPUT_RATE", timeout=15
        )

    @parameterized.expand(parameterized_list(TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_high_limit_set_via_backdoor_THEN_high_lim_updates(self, _, val):
        self._lewis.backdoor_run_function_on_device("set_high_lim", [SENSORS[0], val])
        self.ca.assert_that_pv_is_number("A01:HILIM", val, tolerance=0.05, timeout=15)

    @parameterized.expand(parameterized_list(TEST_VALUES))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_low_limit_set_via_backdoor_THEN_low_lim_updates(self, _, val):
        self._lewis.backdoor_run_function_on_device("set_low_lim", [SENSORS[0], val])
        self.ca.assert_that_pv_is_number("A01:LOWLIM", val, tolerance=0.05, timeout=15)
