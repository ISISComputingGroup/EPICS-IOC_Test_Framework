import unittest

from parameterized import parameterized
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
        "emulator": EMULATOR_NAME,
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


class CryoSMSTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=10)

        self.ca.assert_that_pv_exists("DISABLE", timeout=30)

    @parameterized.expand(["TESLA", "AMPS"])
    def test_GIVEN_outputmode_sp_correct_WHEN_outputmode_sp_written_to_THEN_outputmode_changes(self, units):
        self.ca.assert_setting_setpoint_sets_readback(units, "OUTPUTMODE", "OUTPUTMODE:SP", timeout=10)
