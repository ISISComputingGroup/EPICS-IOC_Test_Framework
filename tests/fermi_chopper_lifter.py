import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister

# Internal Address of device (must be 2 characters)
GALIL_ADDR = "128.0.0.0"

# MACROS to use for the IOC
MACROS = {
    "GALILADDR01": GALIL_ADDR,
    "IFCHOPLIFT": " "
}


class Fermi_chopper_lifterTests(unittest.TestCase):
    """
    Tests for the fermi chopper lift.

    There isn't any logic to test in this IOC so this is really just a test that the DB records get loaded.
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("fermi_chopper_lifter")
        self.ca = ChannelAccess(default_timeout=30)
        self.ca.wait_for("MOT:CHOPLIFT:STATUS", timeout=60)

    def test_WHEN_ioc_is_run_THEN_status_record_exists(self):
        # Simulated galil user variables are initialized to zero which maps to "Unknown".
        self.ca.assert_that_pv_is("MOT:CHOPLIFT:STATUS", "Unknown")
