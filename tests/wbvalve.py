import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "WBVALVE_01"

emulator_name = "wbvalve"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("WBVALVE"),
        "macros": {},
        "emulator": emulator_name,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class WbvalveTests(unittest.TestCase):
    """
    Tests for the Wbvalve IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(emulator_name, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device('reset')

    @parameterized.expand(['wb1', 'wb2'])
    def test_GIVEN_an_ioc_WHEN_set_valve_to_wb1on_THEN_status_is_wb1on(self, expected_value):
        self.ca.assert_setting_setpoint_sets_readback(expected_value, 'POS')

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_get_status_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is('POS', ChannelAccess.Alarms.INVALID)
