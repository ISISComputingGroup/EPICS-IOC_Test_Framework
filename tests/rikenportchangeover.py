import os
import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, EPICS_TOP

ADR1 = "001"
ID1 = "RQ1"
ADR2 = "002"
ID2 = "RB1"

IOCS = [
    {
        "name": "RKNPS_01",
        "directory": get_default_ioc_dir("RKNPS"),
        "macros": {
            "ADR1": ADR1,
            "ADR2": ADR2,
            "ID1": ID1,
            "ID2": ID2,
        },
    },
    {
        "name": "COORD_01",
        "directory": get_default_ioc_dir("COORD"),
        "macros": {},
    },
    {
        "name": "SIMPLE",
        "directory": os.path.join(EPICS_TOP, "ISIS", "SimpleIoc", "master", "iocBoot", "iocsimple"),
        "macros": {},
    },
]


class RikenPortChangeoverTests(unittest.TestCase):
    """
    Tests for a riken port changeover.
    """
    def setUp(self):
        self.ca = ChannelAccess()
        # self.ca.wait_for("COORD_01:PSUS:DISABLE:SP", timeout=30)
        self.ca.wait_for("RKNPS_01:RQ1:POWER", timeout=30)

    def test_GIVEN_disable_pv_connected_WHEN_disable_pv_is_high_THEN_power_supplies_not_disabled(self):

        def _set_and_check_disabled_status(disabled):
            self.ca.set_pv_value("SIMPLE:VALUE1", 1 if disabled else 0)
            for id in [ID1, ID2]:
                self.ca.assert_that_pv_is_number("RKNPS_01:{}:POWER:SP.DISP".format(id), 1 if disabled else 0)

        for disabled in [False, True, False]:  # Check both transitions
            _set_and_check_disabled_status(disabled)
