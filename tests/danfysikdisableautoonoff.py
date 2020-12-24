import unittest

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir

from genie_python.genie_cachannel_wrapper import WriteAccessException

from common_tests.danfysik import DanfysikBase, DEVICE_PREFIX, EMULATOR_NAME

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
        },
        "emulator": EMULATOR_NAME,
    },
]

TEST_MODES = [TestModes.RECSIM]

class DanfysikDisableautonoffTest(DanfysikBase, unittest.TestCase):
    """
    Test for disabling danfysik automatic PSU on/off capability. In a seperate file to the other tests
    due to inability to change macro DISABLE_AUTOONOFF at runtime and the fact that most tests require DISABLE_AUTOONOFF
    to be 0. Tests inherited from DanfysikBase.
    """
    def test_WHEN_disableautonoff_true_THEN_autoonoff_cannot_be_set(self):
        self.ca.assert_that_pv_is("AUTOONOFF", "Disabled")
        with self.assertRaises(WriteAccessException, msg="Genie python should notify of DISP being set"):
            self.ca.set_pv_value("AUTOONOFF", "Enabled")
        self.ca.assert_that_pv_is("AUTOONOFF", "Disabled")
