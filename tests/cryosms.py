import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "CRYOSMS_01"
EMULATOR_NAME = "cryogenic_sms"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("CRYOSMS"),
        "emulator" : EMULATOR_NAME,
    },
]


TEST_MODES = [TestModes.DEVSIM]


class CryoSMSTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=10)

        self.ca.assert_that_pv_exists("DISABLE", timeout=30)

    def test_GIVEN_outputmode_sp_correct_WHEN_outputmode_sp_written_to_THEN_outputmode_changes(self):
        # GIVEN
        current_outputmode = self.ca.get_pv_value("OUTPUTMODE")
        self.ca.assert_that_pv_is("OUTPUTMODE:SP", current_outputmode, timeout=30)

        # WHEN
        new_outputmode = "AMPS" if current_outputmode == "TESLA" else "TESLA"
        self.ca.set_pv_value("OUTPUTMODE:SP", new_outputmode)

        # THEN
        self.ca.assert_that_pv_is("OUTPUTMODE", new_outputmode, timeout=10)
