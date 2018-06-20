import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir

# Internal Address of device (must be 2 characters)
from utils.test_modes import TestModes

GALIL_ADDR = "128.0.0.0"


IOCS = [
    {
        "name": "GALIL_01",
        "directory": get_default_ioc_dir("GALIL"),
        "macros": {
            "GALILADDR01": GALIL_ADDR,
            "IFCHOPLIFT": " ",
        },
    },
]


TEST_MODES = [TestModes.DEVSIM]


class FermiChopperLifterTests(unittest.TestCase):
    """
    Tests for the fermi chopper lift.

    There isn't any logic to test in this IOC so this is really just a test that the DB records get loaded.
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("GALIL_01")
        self.ca = ChannelAccess(default_timeout=30)
        self.ca.assert_that_pv_exists("MOT:CHOPLIFT:STATUS", timeout=60)

    def test_WHEN_ioc_is_run_THEN_status_record_exists(self):
        # Simulated galil user variables are initialized to zero which maps to "Unknown".
        self.ca.assert_that_pv_is("MOT:CHOPLIFT:STATUS", "Unknown")
