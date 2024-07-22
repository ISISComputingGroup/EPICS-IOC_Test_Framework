import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "PT2025_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("PT2025"),
        "macros": {},
        "emulator": "pt2025",
    },
]

DATA_LOCKED = ["L11.1111111T", "L22.2222222T", "L33.3333333T"]
DATA_UNLOCKED = ["W12.1243470T", "V12.1242321T", "V12.1242341T"]

TEST_MODES = [TestModes.DEVSIM]


class Pt2025Tests(unittest.TestCase):
    """
    Tests for the Pt2025 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("pt2025", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device("reset_values")

    @parameterized.expand(DATA_LOCKED)
    def test_when_locked_THEN_all_other_Pvs_change_appropriately(self, data):
        self._lewis.backdoor_set_on_device("data", data)
        self.ca.assert_that_pv_is("FIELD:RAW", data)
        self.ca.assert_that_pv_is("LOCKED", "LOCKED")
        self.ca.assert_that_pv_is("FIELD_TESLA", float(data[1:-1]))
        self.ca.assert_that_pv_is("FIELD_GAUSS", float(data[1:-1]) * 10000)

    @parameterized.expand(DATA_UNLOCKED)
    def test_when_not_locked_THEN_all_other_Pvs_do_not_change(self, data):
        self._lewis.backdoor_set_on_device("data", data)
        self.ca.assert_that_pv_is("FIELD:RAW", data)
        self.ca.assert_that_pv_is("LOCKED", "UNLOCKED")
        self.ca.assert_that_pv_is("CALC_FIELD", -1.0)
        self.ca.assert_that_pv_is("FIELD_GAUSS", -1.0)

    @parameterized.expand(DATA_LOCKED)
    def test_when_data_read_THEN_Activity_PV_is_turned_ON_OFF(self, data):
        # set to a opposite value for PV and check later if it has changed
        self.ca.set_pv_value("ACTIVITY_ON", 0)
        self.ca.set_pv_value("ACTIVITY_OFF", 1)

        self._lewis.backdoor_set_on_device("data", data)

        self.ca.assert_that_pv_is("ACTIVITY", 1)
        self.ca.assert_that_pv_is("ACTIVITY_ON", 1)
        self.ca.assert_that_pv_is("ACTIVITY_OFF", 0)
        self.ca.assert_that_pv_is("ACTIVITY", 0, timeout=3)
