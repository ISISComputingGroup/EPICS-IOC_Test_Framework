import unittest
from common_tests.riken_changeover import RikenChangeover
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes

TEST_MODES = [TestModes.RECSIM]

DEVICE_PREFIX = "RKNPS_01"

IOCS = [{
    "name": DEVICE_PREFIX,
    "directory": get_default_ioc_dir("RKNPS"),
    "macros": {
        "CHAIN1_ID1": "RB2",
        "CHAIN1_ADR1": 1,
        "CHAIN1_ID2": "RB2-2",
        "CHAIN1_ADR2": 2,
    },
}]


class RikenRb2ModeChangeoverTests(RikenChangeover, unittest.TestCase):
    """
    Tests for a riken RB2 mode change.

    Main tests are inherited from RikenChangeover
    """
    def get_power_supplies(self):
        return ["RB2", "RB2-2"]

    def get_coord_prefix(self):
        return "RB2C"

    def get_prefix(self):
        return DEVICE_PREFIX

    def get_input_pv(self):
        return "DAQ:R01:DATA"

    def get_acknowledgement_pv(self):
        return "DAQ:W01:DATA"
