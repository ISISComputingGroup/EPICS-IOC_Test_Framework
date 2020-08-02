import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim
import time

DEVICE_PREFIX = "SMTOF70_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SMTOF70"),
        "macros": {},
    },
]

TEST_MODES = [TestModes.RECSIM]

class SumitomoF70Tests(unittest.TestCase):
    """
    Tests for the SMToF70 IOC.
    """
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=5)
        
    def test_WHEN_setup_THEN_values_correct(self):
        self.ca.set_pv_value("SIM:OpHours", 10.0)
        self.ca.set_pv_value("SIM:HeReturnPress", 12.0)
        self.ca.set_pv_value("SIM:HeTemp", 3.0)
        time.sleep(5)
        self.ca.assert_that_pv_is("Firmware", "test firmware")
        self.ca.assert_that_pv_is("OpHours", 10.0)
        self.ca.assert_that_pv_is("HeReturnPress", 12.0)
        self.ca.assert_that_pv_is("HeTemp", 3.0)
