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
        "CHAIN1_ID1": "RQ18",
        "CHAIN1_ADR1": 1,

        "CHAIN1_ID2": "RQ19",
        "CHAIN1_ADR2": 2,

        "CHAIN2_ID1": "RQ20",
        "CHAIN2_ADR1": 1,
    },
    "pv_for_existence": "RQ18:POWER",
}]


class RikenPortChangeoverTests(RikenChangeover, unittest.TestCase):
    """
    Tests for a riken port changeover.

    Main tests are inherited from RikenChangeover
    """
    def get_power_supplies(self):
        return ["RQ18", "RQ19", "RQ20"]

    def get_coord_prefix(self):
        return "PC"

    def get_prefix(self):
        return DEVICE_PREFIX

    def get_input_pv(self):
        return "DAQ:R00:DATA"

    def get_acknowledgement_pv(self):
        return "DAQ:W00:DATA"
