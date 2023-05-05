import unittest

from parameterized import parameterized

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from common_tests.eurotherm import (EurothermBaseTests, NONE_TXT_CALIBRATION_MIN_TEMPERATURE,
                                    NONE_TXT_CALIBRATION_MAX_TEMPERATURE)
from utils.calibration_utils import use_calibration_file

# Internal Address of device (must be 2 characters)
ADDRESS = "A01"
# Numerical address of the device
ADDR_1 = "01" # Leave this value as 1 when changing the ADDRESS value above - hard coded in LEWIS emulator
DEVICE = "EUROTHRM_01"

EMULATOR_DEVICE = "eurotherm"

IOCS = [
    {
        "name": DEVICE,
        "directory": get_default_ioc_dir("EUROTHRM"),
        "ioc_launcher_class": ProcServLauncher,
        "macros": {
            "COMMS_MODE": "eibisynch",
            "ADDR": ADDRESS,
            "ADDR_1": ADDR_1,
            "ADDR_2": "",
            "ADDR_3": "",
            "ADDR_4": "",
            "ADDR_5": "",
            "ADDR_6": "",
            "ADDR_7": "",
            "ADDR_8": "",
            "ADDR_9": "",
            "ADDR_10": ""
        },
        "emulator": EMULATOR_DEVICE,
    },
]


TEST_MODES = [TestModes.DEVSIM]


class EurothermTests(EurothermBaseTests, unittest.TestCase):
    def get_device(self):
        return DEVICE

    def get_emulator_device(self):
        return EMULATOR_DEVICE

    @parameterized.expand([
        ("over_range_calc_pv_is_over_range", NONE_TXT_CALIBRATION_MAX_TEMPERATURE + 5.0, 1.0),
        ("over_range_calc_pv_is_within_range", NONE_TXT_CALIBRATION_MAX_TEMPERATURE - 200, 0.0),
        ("over_range_calc_pv_is_within_range", NONE_TXT_CALIBRATION_MAX_TEMPERATURE, 0.0)
    ])
    def test_GIVEN_None_txt_calibration_file_WHEN_temperature_is_set_THEN(
            self, _, temperature, expected_value_of_over_range_calc_pv):
        """
        Note: this test can only run on BISYNCH eurotherms, modbus max temperature is 6553.5 but ramp file goes up
        to 10,000 and this test attempts to check this behaviour
        """
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
        """
        Note: this test can only run on BISYNCH eurotherms, modbus max temperature is 6553.5 but ramp file goes up
        to 10,000 and this test attempts to check this behaviour
        """
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

    def test_GIVEN_simulated_reply_delay_in_emulator_WHEN_consecutive_read_commands_THEN_all_reads_correct(self):
        for temp in range(1, 20):
            self._set_setpoint_and_current_temperature(float(temp))
            self.ca.assert_that_pv_is("RBV", float(temp))
