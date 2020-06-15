import unittest

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir

from common_tests.danfysik import DanfysikBase, DEVICE_PREFIX, EMULATOR_NAME


# Arbitrary - normal danfysik full scale is 1000000, set it a little bit lower so we can tell the limit is working.
MAX_RAW_SETPOINT = 987654

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DFKPS"),
        "macros": {
            "CALIBRATED": "1",
            "LOCAL_CALIB": "no",
            "CALIB_FILE": "default_calib.dat",  # 1:1 calibration useful for testing
            "MAX_RAW_SETPOINT": MAX_RAW_SETPOINT,
            "FACTOR_READ_I": 1,
            "FACTOR_WRITE_I": 1,
        },
        "emulator": EMULATOR_NAME,
        "lewis_protocol": "model8000",
        "DISABLE_AUTOONOFF": "0",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class DanfysikCommonCalibTests(DanfysikBase, unittest.TestCase):
    """
    Tests for calibrated danfysik. Tests inherited from DanfysikBase.
    """
    def test_GIVEN_local_calib_macro_set_to_no_THEN_calib_base_dir_is_common_dir(self):
        for pv in ["FIELD:CALIB", "FIELD:SP:CALIB"]:
            self.ca.assert_that_pv_is("{}.TDIR".format(pv), r"magnets")
            self.ca.assert_that_pv_is("{}.BDIR".format(pv), r"C:/Instrument/Settings/config/common")

    def test_GIVEN_a_requested_current_which_is_too_big_WHEN_calibrated_THEN_current_setpoint_sent_to_danfysik_is_not_bigger_than_max(self):
        # Request a field above the maximum raw setpoint
        self.ca.set_pv_value("FIELD:SP", 10 * MAX_RAW_SETPOINT)

        # Ensure that the field was capped at 1000000 ppm (i.e. 100% of the danfysik's full scale)
        self.ca.assert_that_pv_is_number("FIELD", MAX_RAW_SETPOINT, tolerance=0.1)

    def test_GIVEN_maximum_current_requested_THEN_current_not_in_alarm(self):
        self.ca.set_pv_value("FIELD:SP", MAX_RAW_SETPOINT)
        self.ca.assert_that_pv_is_number("FIELD", MAX_RAW_SETPOINT, tolerance=0.1)
        self.ca.assert_that_pv_alarm_is("FIELD", self.ca.Alarms.NONE)
