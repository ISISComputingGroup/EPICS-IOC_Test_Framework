import unittest
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

DEVICE_PREFIX = "TEKOSC_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TEKOSC"),
        "macros": {},
        "emulator": "tekosc",
    },
]


TEST_MODES = [TestModes.DEVSIM]


class TekOsc(unittest.TestCase):
    """
    Tests for the Tektronix Oscilloscope IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tekosc", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0, default_timeout=10)
        self._lewis.backdoor_set_on_device('connected', True)

    def test_GIVEN_nothing_WHEN_get_identity_THEN_identity_returned(self):
        identity_string = "TEKTRONIX,DPO3054,C012754,SCPI:99.0 FV:1.0"

        self.ca.assert_that_pv_is("IDN", identity_string[:39])  # limited string size
