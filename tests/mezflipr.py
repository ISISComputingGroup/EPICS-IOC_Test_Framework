import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "MEZFLIPR_01"
EMULATOR_NAME = "mezflipr"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MEZFLIPR"),
        "emulator": EMULATOR_NAME,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class MezfliprTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)

        self._lewis.backdoor_set_on_device("connected", True)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @skip_if_recsim("Disconnection simulation not implemented in recsim")
    def test_GIVEN_device_is_connected_THEN_can_read_id(self):
        self.ca.assert_that_pv_is("ID", "Simulated mezei flipper")
        self.ca.assert_that_pv_alarm_is("ID", self.ca.Alarms.NONE)

        self._lewis.backdoor_set_on_device("connected", False)
        self.ca.assert_that_pv_alarm_is("ID", self.ca.Alarms.INVALID)
