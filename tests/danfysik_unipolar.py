import unittest

from common_tests.danfysik import DEVICE_PREFIX, EMULATOR_NAME, DanfysikBase
from utils.ioc_launcher import ProcServLauncher, get_default_ioc_dir
from utils.test_modes import TestModes

MAX_RAW_SETPOINT = 1000000
MIN_RAW_SETPOINT = 0

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DFKPS"),
        "macros": {
            "DEV_TYPE": "8000",
            "CALIBRATED": "0",
            "FACTOR_READ_I": "1",
            "FACTOR_READ_V": "1",
            "FACTOR_WRITE_I": "1",
            "DISABLE_AUTOONOFF": "1",
            "POLARITY": "UNIPOLAR",
            "MAX_RAW_SETPOINT": MAX_RAW_SETPOINT,
        },
        "emulator": EMULATOR_NAME,
        "lewis_protocol": "model8000",
        "ioc_launcher_class": ProcServLauncher,
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class DanfysikUnipolarTest(DanfysikBase, unittest.TestCase):
    """
    Tests for unipolar danfysik. Separate test class as macros cannot be set at runtime.
    """

    def test_GIVEN_polarity_is_unipolar_WHEN_setting_negative_current_THEN_current_is_set_to_zero(
        self,
    ):
        # set to non-zero value initially to test minimum value is actually set
        initial_curr = 10
        self.ca.set_pv_value("CURR:SP", initial_curr)
        self.ca.assert_that_pv_is("RAW:SP", initial_curr)
        self.ca.assert_that_pv_is("RAW", initial_curr)

        self.ca.set_pv_value("CURR:SP", MAX_RAW_SETPOINT * (-1))

        self.ca.assert_that_pv_is("RAW:SP", 0)
        self.ca.assert_that_pv_is("RAW", MIN_RAW_SETPOINT)
