import unittest

from parameterized import parameterized

from genie_python.genie_cachannel_wrapper import InvalidEnumStringException

from common_tests.tpgx00 import Tpgx00Base
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import skip_if_recsim, parameterized_list
from enum import Enum


DEVICE_PREFIX = "TPG300_01"

IOCS = [
    {
    "name": DEVICE_PREFIX,
    "directory": get_default_ioc_dir("TPG300"),
    "macros": {
        "MODEL": "300"
    },
    "emulator": "tpgx00",
    "lewis_protocol": "tpg300",
    "pv_for_existence": "UNITS",
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]

SWITCHING_FUNCTIONS = ("SEL", "1", "2", "3", "4", "A", "B")


class SFAssignment(Enum):
    OFF         = (0, "No assignment")
    A1          = (1, "A1")
    A2          = (2, "A2")
    B1          = (3, "B1")
    B2          = (4, "B1")
    A1_SELF_MON = (5, "A1 self-monitor")
    A2_SELF_MON = (6, "A2 self-monitor")
    B1_SELF_MON = (7, "B1 self-monitor")
    B2_SELF_MON = (8, "B1 self-monitor")

    def __new__(cls, value, desc):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.desc = desc
        return obj


class Units(Enum):
    mbar = 1
    Torr = 2
    Pa = 3


class Tpg300Tests(Tpgx00Base, unittest.TestCase):
    """
    Tests for the TPG300.
    """

    def get_prefix(self):
        return DEVICE_PREFIX
        
    def get_units(self):
        return Units

    def get_sf_assignment(self):
        return SFAssignment
    
    def get_switching_fns(self):
        return SWITCHING_FUNCTIONS
