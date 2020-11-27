import unittest

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from utils.testing import skip_if_recsim

from time import sleep

from common_tests.danfysik import DanfysikCommon, DEVICE_PREFIX, EMULATOR_NAME, POWER_STATES

MAX_RAW_SETPOINT = 1000000
MIN_RAW_SETPOINT = MAX_RAW_SETPOINT * (-1)

DEVICE_ADDRESS = 75

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DFKPS"),
        "macros": {
            "DEV_TYPE": "8500",
            "CALIBRATED": "0",
            "FACTOR_READ_I": "1",
            "FACTOR_READ_V": "1",
            "FACTOR_WRITE_I": "1",
            "ADDRESS": DEVICE_ADDRESS,
            "DISABLE_AUTOONOFF": "0",
            "MAX_RAW_SETPOINT": MAX_RAW_SETPOINT,
            "POLARITY": "BIPOLAR",
        },
        "emulator": EMULATOR_NAME,
        "lewis_protocol": "model8500",
        "ioc_launcher_class": ProcServLauncher,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Danfysik8500Tests(DanfysikCommon, unittest.TestCase):
    """
    Tests for danfysik model 8500. Tests inherited from DanfysikBase.
    """

    def get_emulator_address(self):
        """
        Gets the PSU address of the emulator

        Returns:
            emulator_address: int, the PSU address of the emulator
        """

        emulator_address = int(self._lewis.backdoor_get_from_device("currently_addressed_psu"))

        return emulator_address

    def set_to_incorrect_address(self):
        """
        Sets the emulator address to a different address to the IOC

        Returns:
            None
        """

        different_address = DEVICE_ADDRESS + 1

        self._lewis.backdoor_run_function_on_device("set_address", [different_address, ])

        emulator_address = self.get_emulator_address()

        self.ca.assert_that_pv_is_not_number("ADDRESS", emulator_address, tolerance=0.1)

    def set_to_correct_address(self):
        """
        Sets the device emulator to the same PSU address as the IOC

        Returns:
            None
        """
        self._lewis.backdoor_set_on_device("address", DEVICE_ADDRESS)
        self._lewis.backdoor_run_function_on_device("set_address", [DEVICE_ADDRESS, ])

        emulator_address = self.get_emulator_address()

        self.assertEqual(emulator_address, DEVICE_ADDRESS)

    def test_GIVEN_ioc_THEN_model_is_set_correctly(self):
        self.ca.assert_that_pv_is("DEV_TYPE", "8500")

    @skip_if_recsim("Uses lewis back door")
    def test_GIVEN_device_set_to_an_address_WHEN_IOC_addresses_that_PSU_THEN_device_responds(self):
        self.set_to_correct_address()
        for pol in POWER_STATES:
            self.ca.assert_setting_setpoint_sets_readback(pol, "POWER")

    @skip_if_recsim("Uses lewis back door")
    def test_GIVEN_device_not_at_correct_address_WHEN_current_requested_THEN_device_does_not_respond(self):
        self.ca.assert_that_pv_alarm_is("POWER", self.ca.Alarms.NONE)
        self.set_to_incorrect_address()

        self.ca.assert_that_pv_alarm_is("POWER", self.ca.Alarms.INVALID)

        self.set_to_correct_address()

    @skip_if_recsim("Uses lewis back door")
    def test_GIVEN_device_not_at_correct_address_THEN_ioc_changes_device_address(self):
        self.set_to_incorrect_address()

        self.ca.assert_that_pv_is_not("ADDRESS", self.get_emulator_address())

        timeout = 30

        for i in range(timeout):
            if self.get_emulator_address() == DEVICE_ADDRESS:
                break
            else:
                sleep(1.0)

        self.ca.assert_that_pv_is("ADDRESS", self.get_emulator_address())

        self.set_to_correct_address()

    def test_GIVEN_polarity_is_bipolar_WHEN_setting_current_THEN_min_setpoint_is_negative_of_max_setpoint(self):
        self.ca.set_pv_value("CURR:SP", MIN_RAW_SETPOINT * 2)

        self.ca.assert_that_pv_is("CURR:SP:RBV", MIN_RAW_SETPOINT)
        self.ca.assert_that_pv_is("CURR", MIN_RAW_SETPOINT)