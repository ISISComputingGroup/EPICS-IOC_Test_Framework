import contextlib
import unittest

from parameterized import parameterized
from utils.emulator_launcher import LewisLauncher

from common_tests.eurotherm import (
    NONE_TXT_CALIBRATION_MAX_TEMPERATURE,
    NONE_TXT_CALIBRATION_MIN_TEMPERATURE,
    EurothermBaseTests,
)
from utils.calibration_utils import use_calibration_file
from utils.ioc_launcher import ProcServLauncher, get_default_ioc_dir
from utils.test_modes import TestModes

DEVICE = "EUROTHRM_01"
EMULATOR = "eurotherm"
SCALING = "1.0"
TEST_MODES = [TestModes.DEVSIM]
IOCS = [
    {
        "name": DEVICE,
        "directory": get_default_ioc_dir("EUROTHRM"),
        "ioc_launcher_class": ProcServLauncher,
        "macros": {
            "COMMS_MODE": "eibisynch",
            "ADDR_1": "01",
            "ADDR_2": "02",
            "ADDR_3": "03",
            "ADDR_4": "04",
            "ADDR_5": "05",
            "ADDR_6": "06",
            "ADDR_7": "",
            "ADDR_8": "",
            "ADDR_9": "",
            "ADDR_10": "",
        },
        "emulator": EMULATOR,
    },
]


class EurothermTests(EurothermBaseTests, unittest.TestCase):
    def setUp(self):
        super(EurothermTests, self).setUp()
        self._lewis.backdoor_run_function_on_device("set_scaling", ["01", 1.0])
        self._lewis:LewisLauncher

    def get_device(self):
        return DEVICE

    def get_emulator_device(self):
        return EMULATOR

    def get_scaling(self):
        return SCALING

    def _get_temperature_setter_wrapper(self):
        return contextlib.nullcontext()

    @parameterized.expand(
        [
            ("over_range_calc_pv_is_over_range", NONE_TXT_CALIBRATION_MAX_TEMPERATURE + 5.0, 1.0),
            ("over_range_calc_pv_is_within_range", NONE_TXT_CALIBRATION_MAX_TEMPERATURE - 200, 0.0),
            ("over_range_calc_pv_is_within_range", NONE_TXT_CALIBRATION_MAX_TEMPERATURE, 0.0),
        ]
    )
    def test_GIVEN_None_txt_calibration_file_WHEN_temperature_is_set_THEN(
        self, _: str, temperature: float, exp_val: float
    ) -> None:
        """
        Note: this test can only run on BISYNCH eurotherms, modbus max temperature is 6553.5 but ramp file goes up
        to 10,000 and this test attempts to check this behaviour
        """
        # Arrange

        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt", prefix="A01:"):
            self.ca.assert_that_pv_exists("A01:CAL:RANGE")
            self.ca.assert_that_pv_is("A01:TEMP:RANGE:OVER.B", NONE_TXT_CALIBRATION_MAX_TEMPERATURE)

            # Act:
            self._set_setpoint_and_current_temperature(temperature)

            # Assert
            self.ca.assert_that_pv_is("A01:TEMP:RANGE:OVER.A", temperature)
            self.ca.assert_that_pv_is("A01:TEMP:RANGE:OVER", expected_value=exp_val)

    def test_GIVEN_None_txt_calib_file_WHEN_changed_to_C006_calib_file_THEN_the_calib_limits_change(
        self,
    ) -> None:
        """
        Note: this test can only run on BISYNCH eurotherms,
        modbus max temperature is 6553.5 but ramp file goes up
        to 10,000 and this test attempts to check this behaviour
        """
        c006_calibration_file_max = 330.26135292267900000000
        c006_calibration_file_min = 1.20927230303971000000

        # Arrange
        self._assert_using_mock_table_location()
        with use_calibration_file(self.ca, "None.txt", prefix="A01:"):
            self.ca.assert_that_pv_exists("A01:CAL:RANGE")
            self.ca.assert_that_pv_is("A01:TEMP:RANGE:OVER.B", NONE_TXT_CALIBRATION_MAX_TEMPERATURE)
            self.ca.assert_that_pv_is(
                "A01:TEMP:RANGE:UNDER.B", NONE_TXT_CALIBRATION_MIN_TEMPERATURE
            )

        # Act:
        with use_calibration_file(self.ca, "C006.txt", prefix="A01:"):
            # Assert
            self.ca.assert_that_pv_is("A01:TEMP:RANGE:OVER.B", c006_calibration_file_max)
            self.ca.assert_that_pv_is("A01:TEMP:RANGE:UNDER.B", c006_calibration_file_min)

    def test_GIVEN_sim_delay_WHEN_temp_read_from_many_sensors_THEN_all_reads_correct(self) -> None:
        self._lewis.backdoor_run_function_on_device("set_delay_time", ["01", (300 / 1000)])
        for id in range(1, 7):
            pv_sensor = f"A{id:02}"
            sensor = f"{id:02}"

            for temp in range(1, 3):
                self._lewis.backdoor_run_function_on_device(
                    "set_current_temperature", [sensor, float(temp)]
                )
                self.ca.assert_that_pv_is(f"{pv_sensor}:RBV", float(temp))

        self._lewis.backdoor_run_function_on_device("set_delay_time", [None, 0.0])

    def test_GIVEN_sim_delay_WHEN_temp_set_on_multiple_sensors_THEN_all_reads_correct(self) -> None:
        self._lewis.backdoor_run_function_on_device("set_delay_time", ["01", (300 / 1000)])
        for id in range(1, 7):
            sensor = f"A{id:02}"
            for temp in range(1, 3):
                self._set_setpoint_and_current_temperature(float(temp), sensor=sensor)
                self.ca.assert_that_pv_is(f"{sensor}:RBV", float(temp), timeout=30.0)

        self._lewis.backdoor_run_function_on_device("set_delay_time", [None, 0.0])

    def test_GIVEN_many_sensors_WHEN_one_sensor_disconnect_THEN_other_sensors_read_ok(self) -> None:
        # Ensure that A02 is connected
        self._lewis.backdoor_run_function_on_device("set_connected", ["02", True])

        # Disconnect A01 and check PV for A01 is in alarm, and PV for A02 is not:
        with self._lewis.backdoor_simulate_disconnected_addr():
            self.ca.assert_that_pv_alarm_is("A01:TEMP", self.ca.Alarms.INVALID, timeout=30)
            self.ca.assert_that_pv_alarm_is_not("A02:TEMP", self.ca.Alarms.INVALID, timeout=30)

        # Ensure that after backdoor_run_function, the PV for A01 gets reconnected:
        self.ca.assert_that_pv_alarm_is("A01:TEMP", self.ca.Alarms.NONE, timeout=30)
