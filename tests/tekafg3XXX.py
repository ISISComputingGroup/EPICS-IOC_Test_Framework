import unittest
from parameterized import parameterized
import itertools
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

DEVICE_PREFIX = "TEKAFG3XXX_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TEKAFG3XXX"),
        "macros": {},
        "emulator": "tekafg3XXX",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Tekafg3XXXTests(unittest.TestCase):
    """
    Tests for the Afg3021B IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tekafg3XXX", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device('connected', True)

    @skip_if_recsim("Only set on PINI so can not test in framework")
    def test_GIVEN_nothing_WHEN_get_identity_THEN_identity_returned(self):
        identity_string = "TEKTRONIX,AFG3021,C100101,SCPI:99.0 FV:1.0"

        self.ca.assert_that_pv_is("IDN", identity_string[:39])  # limited string size

    @skip_if_recsim("Uses lewis backdoor")
    def test_GIVEN_nothing_WHEN_triggering_device_THEN_device_is_triggered(self):
        self._lewis.backdoor_run_function_on_device("trigger", [])
        self._lewis.assert_that_emulator_value_is("triggered", 'True')
