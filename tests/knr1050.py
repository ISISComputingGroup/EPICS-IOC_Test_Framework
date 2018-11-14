import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "KNR1050_01"

device_name = "knr1050"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KNR1050"),
        "macros": {},
        "emulator": device_name,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Knr1050Tests(unittest.TestCase):
    """
    Tests for the Knr1050 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(device_name, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        #self._lewis.backdoor_run_function_on_device("reset")

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_an_IOC_WHEN_stop_issued_THEN_device_stops(self):
        stopped_status = self._lewis.backdoor_get_from_device("is_stopped")
        self.assertEqual(stopped_status, "False")
        self.ca.set_pv_value("STOP:SP", 1)

        stopped_status = self._lewis.backdoor_get_from_device("is_stopped")
        self.assertEqual(stopped_status, "True")