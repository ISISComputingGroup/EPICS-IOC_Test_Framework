import unittest
import time

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes

IOCS = [
    {
        "name": "LINMOT_01",
        "directory": get_default_ioc_dir("LINMOT"),
        "macros": {
            "AXIS1": "yes",
            "MTRCTRL": "01",
        },
    },
]


TEST_MODES = [TestModes.RECSIM]

MTR = "MOT:MTR0101"


class MotSimTests(unittest.TestCase):
    def setUp(self):
        self._ioc = IOCRegister.get_running("mot_sim")
        self.ca = ChannelAccess(default_timeout=30)

        self.ca.wait_for(MTR)

    def test_stop(self):
        self.ca.set_pv_value(MTR + ".VBAS", 0)
        self.ca.set_pv_value(MTR + ".ACCL", 0.01)

        self.ca.set_pv_value(MTR, 0.0)

        self.ca.assert_that_pv_is_number(MTR + ".DMOV", 1) # Motor stopped

        self.ca.set_pv_value(MTR, 50.0)

        time.sleep(5)

        for _ in range(10):
            self.ca.set_pv_value(MTR + ".STOP", 1)

        print("PV IS AT {}".format(self.ca.get_pv_value(MTR + ".RBV")))

        self.ca.assert_that_pv_is_not_number(MTR + ".RBV", 0.0, 0.1)
        self.ca.assert_that_pv_is_not_number(MTR + ".RBV", 50.0, 0.1)