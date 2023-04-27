import unittest

from common_tests.tpgx00 import Tpgx00Base
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from enum import Enum


DEVICE_PREFIX = "TPG300_01"
# DEVICE_EMULATOR = "tpg500"

IOCS = [
    {
    "name": DEVICE_PREFIX,
    "directory": get_default_ioc_dir("TPG300"),
    "macros": {},
    "emulator": "tpg300",
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


class Units(Enum):
    hPa = 0
    mbar = 1
    Torr = 2
    Pa = 3
    Micron = 4
    Volt = 5
    Amp = 6


class Tpg500Tests(Tpgx00Base, unittest.TestCase):
    """
    Tests for the TPG500.
    """

    def get_prefix(self):
        return DEVICE_PREFIX

    # def get_emulator(self):
    #     return DEVICE_EMULATOR
    
    def get_units(self):
        return Units