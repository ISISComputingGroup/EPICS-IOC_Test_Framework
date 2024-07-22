import os
import unittest

from utils.channel_access import ChannelAccess
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "SPINFLIPPER_01"
EPICS_TOP = os.environ.get("KIT_ROOT", os.path.join("C:\\", "Instrument", "Apps", "EPICS"))

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(
            EPICS_TOP, "ioc", "master", "SPINFLIPPER306015", "iocBoot", "iocSPINFLIPPER-IOC-01"
        ),
        "macros": {},
        "emulator": "Spinflipper",
    },
]


TEST_MODES = [TestModes.RECSIM]


class SpinflipperTests(unittest.TestCase):
    """
    Tests for the Spinflipper IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Spinflipper", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_max_guide_temp_set_WHEN_read_THEN_max_temp_is_as_expected(self):
        test_value = 150
        self.ca.assert_setting_setpoint_sets_readback(
            test_value, "MAXTCOIL", "MAXTCOIL:SP", test_value
        )
