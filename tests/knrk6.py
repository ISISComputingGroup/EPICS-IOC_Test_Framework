import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "KNRK6_01"
DEVICE_NAME = "knrk6"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KNRK6"),
        "macros": {},
        "emulator": DEVICE_NAME,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Knrk6Tests(unittest.TestCase):
    """
    Tests for the Knrk6 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("POSITION", timeout=30)
        self._lewis.backdoor_run_function_on_device("reset")

    def test_GIVEN_home_position_THEN_home_position_returned(self):
        expected_value = 1
        self.ca.set_pv_value("POSITION:SP", expected_value)

        self.ca.assert_that_pv_is("POSITION", expected_value, timeout=5)

    def test_GIVEN_set_position_THEN_moved_to_correct_position(self):
        expected_value = 6
        self.ca.set_pv_value("POSITION:SP", expected_value)

        self.ca.assert_that_pv_is("POSITION", expected_value, timeout=5)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_device_not_connected_WHEN_get_error_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is('POSITION', ChannelAccess.Alarms.INVALID, timeout=5)
