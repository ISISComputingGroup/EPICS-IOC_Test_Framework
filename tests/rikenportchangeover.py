import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.ioc_launcher import get_default_ioc_dir


IOCS = [
    {
        "name": "COORD_01",
        "directory": get_default_ioc_dir("COORD"),
        "macros": {

        },
    },
    {
        "name": "DFKPS_01",
        "directory": get_default_ioc_dir("DFKPS"),
        "macros": {

        },
    },
    {
        "name": "DFKPS_02",
        "directory": get_default_ioc_dir("DFKPS", 2),
        "macros": {

        },
    },
]


class RikenportchangeoverTests(unittest.TestCase):
    """
    Tests for a riken port changeover.
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("rikenPortChangeover")
        self.ca = ChannelAccess()
        self.ca.wait_for("COORD_01:PSUS:DISABLE:SP", timeout=30)

    def test_GIVEN_a_WHEN_b_THEN_c(self):
        self.ca.assert_that_pv_is("COORD_01:PSUS:DISABLE:SP", "ENABLED")
