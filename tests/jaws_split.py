import os
from collections import OrderedDict

import unittest

from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes

from .jaws import JawsTestsBase

MTR_01 = "GALIL_01"
MTR_02 = "GALIL_02"

test_path = os.path.realpath(
    os.path.join(os.getenv("EPICS_KIT_ROOT"), "support", "jaws", "master", "settings", "jaws_full_split"))

IOCS = [
    {
        "name": MTR_01,
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "AXIS1",
        "macros": {
            "MTRCTRL": "01",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        },
    },
    {
        "name": MTR_02,
        "directory": get_default_ioc_dir("GALIL", iocnum=2),
        "pv_for_existence": "AXIS1",
        "macros": {
            "MTRCTRL": "02",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        },
    },
]

TEST_MODES = [TestModes.DEVSIM]


class SplitJawsTests(JawsTestsBase, unittest.TestCase):
    """
    Tests for jaws split over multiple controllers
    """

    def setup_jaws(self):
        self.MTR_NORTH = "MOT:MTR0101"
        self.MTR_SOUTH = "MOT:MTR0102"
        self.MTR_WEST = "MOT:MTR0201"
        self.MTR_EAST = "MOT:MTR0202"
        self.UNDERLYING_MTRS = OrderedDict([("N", self.MTR_NORTH),
                                            ("S", self.MTR_SOUTH),
                                            ("E", self.MTR_WEST),
                                            ("W", self.MTR_EAST)])
