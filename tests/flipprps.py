import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "FLIPPRPS_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("FLIPPRPS"),
        "macros": {},
        "emulator": "flipprps",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class FlipprpsTests(unittest.TestCase):
    """
    Tests for the Flipprps IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("flipprps", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device("connected", True)

    @skip_if_recsim("Lewis backdoor commands not available in RecSim")
    def test_SET_polarity(self):
        self.ca.set_pv_value("POLARITY", "Down")
        self._lewis.assert_that_emulator_value_is("polarity", '0')
        self.ca.set_pv_value("POLARITY", "Up")
        self._lewis.assert_that_emulator_value_is("polarity", '1')

    def test_GET_id(self):
        self.ca.assert_that_pv_is("ID", "Flipper")

    @skip_if_recsim("Lewis backdoor commands not available in RecSim")
    def test_GIVEN_device_not_connected_THEN_id_is_in_alarm(self):
        self._lewis.backdoor_set_on_device("connected", False)
        self.ca.assert_that_pv_alarm_is("ID", self.ca.Alarms.INVALID, 20)

    @skip_if_recsim("Lewis backdoor commands not available in RecSim")
    def test_GIVEN_device_not_connected_THEN_polarity_raises_timeout_alarm_after_set(self):
        self._lewis.backdoor_set_on_device("connected", False)
        self.ca.set_pv_value("POLARITY", "Up")
        self.ca.assert_that_pv_alarm_is("POLARITY", self.ca.Alarms.INVALID)
