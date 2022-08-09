import unittest

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from common_tests.eurotherm import EurothermBaseTests

# Internal Address of device (must be 2 characters)
ADDRESS = "A01"
# Numerical address of the device
ADDR_1 = 1 # Leave this value as 1 when changing the ADDRESS value above - hard coded in LEWIS emulator
DEVICE = "EUROTHRM_01"

EMULATOR_DEVICE = "eurotherm"

IOCS = [
    {
        "name": DEVICE,
        "directory": get_default_ioc_dir("EUROTHRM"),
        "ioc_launcher_class": ProcServLauncher,
        "macros": {
            "ADDR": ADDRESS,
            "ADDR_1": ADDR_1,
            "ADDR_2": "",
            "ADDR_3": "",
            "ADDR_4": "",
            "ADDR_5": "",
            "ADDR_6": "",
            "ADDR_7": "",
            "ADDR_8": "",
            "ADDR_9": "",
            "ADDR_10": ""
        },
        "emulator": EMULATOR_DEVICE,
    },
]


TEST_MODES = [TestModes.DEVSIM]


class EurothermTests(EurothermBaseTests, unittest.TestCase):
    def get_address(self):
        return ADDRESS

    def get_device(self):
        return DEVICE

    def get_emulator_device(self):
        return EMULATOR_DEVICE
