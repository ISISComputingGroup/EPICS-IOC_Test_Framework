import unittest
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

DEVICE_PREFIX = "TEKAFG3XXX_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TEKAFG3XXX"),
        "macros": {},
        "emulator": "tekafg3XXX",
    },
]


TEST_MODES = [TestModes.DEVSIM]


class Tekafg3XXXTests(unittest.TestCase):
    """
    Tests for the Afg3021B IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tekafg3XXX", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0)
        self._lewis.backdoor_set_on_device('connected', True)

    def test_GIVEN_nothing_WHEN_get_identity_THEN_identity_returned(self):
        identity_string = "TEKTRONIX,AFG3021,C100101,SCPI:99.0 FV:1.0"

        self.ca.assert_that_pv_is("IDN", identity_string[:39])  # limited string size

    def test_GIVEN_nothing_WHEN_triggering_device_THEN_device_is_triggered(self):
        self._lewis.backdoor_set_and_assert_set("triggered", 'False')
        self.ca.set_pv_value("TRIGGER", True)
        self._lewis.assert_that_emulator_value_is("triggered", 'True')
