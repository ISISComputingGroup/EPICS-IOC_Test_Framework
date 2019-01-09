import unittest

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir

from common_tests.danfysik import DanfysikBase, DEVICE_PREFIX, EMULATOR_NAME

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DFKPS"),
        "macros": {
            "CALIBRATED": "1",
            "LOCAL_CALIB": "no"
        },
        "emulator": EMULATOR_NAME,
        "emulator_protocol": "model8000",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

class DanfysikCommonCalibTests(DanfysikBase, unittest.TestCase):
    """
    Tests for danfysik model 8000. Tests inherited from DanfysikBase.
    """
    def test_GIVEN_local_calib_macro_set_to_no_THEN_calib_base_dir_is_common_dir(self):
        for pv in ["FIELD:CALIB", "FIELD:SP:CALIB"]:
            self.ca.assert_that_pv_is("{}.TDIR".format(pv), r"magnets")
            self.ca.assert_that_pv_is("{}.BDIR".format(pv), r"C:/Instrument/Settings/config/common")
