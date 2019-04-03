import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "CHTOBISR_01"
EMULATOR = "chtobisr"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("CHTOBISR"),
        "emulator": EMULATOR,
    },
]


# TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]
TEST_MODES = [TestModes.DEVSIM]

ON_OFF = {True: "ON", False: "OFF"}


class ChtobisrTests(unittest.TestCase):
    """
    Tests for the Coherent OBIS Laser Remote IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)
        self._lewis.backdoor_set_on_device("connected", True)

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_ID_requested_WHEN_device_connected_THEN_ID_is_returned(self):
        expected_value = "Coherent OBIS Laser Remote - EMULATOR"
        self._lewis.backdoor_set_on_device("id", expected_value)
        self.ca.assert_that_pv_is("ID", expected_value)

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_ID_requested_WHEN_device_disconnected_THEN_alarm_is_raised(self):
        self._lewis.backdoor_set_on_device("connected", False)
        self.ca.assert_that_pv_alarm_is("ID", self.ca.Alarms.INVALID)
