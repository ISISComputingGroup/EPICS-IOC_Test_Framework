import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "LINKAM95_01"

EMULATOR_NAME = "linkam_t95"
IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LINKAM95"),
        "macros": {},
        "emulator": EMULATOR_NAME,
    },
]

TEST_MODES = [TestModes.DEVSIM]


class Linkam95Tests(unittest.TestCase):
    """
    Tests for the Linkam95 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_a_valid_temperature_to_set_WHEN_set_THEN_display_temperature_is_valid_temperature(
        self,
    ):
        expected_temp = 10

        self._lewis.backdoor_set_on_device("temperature", expected_temp)

        self.ca.assert_that_pv_is("TEMP", expected_temp)
