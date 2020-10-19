import os
from collections import OrderedDict

import unittest

from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes

from .jaws import JawsTestsBase

DEVICE_PREFIX = "GALILMUL_01"

test_path = os.path.realpath(
    os.path.join(os.getenv("EPICS_KIT_ROOT"), "support", "jaws", "master", "settings", "jaws_galilmul"))

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("GALILMUL"),
        "pv_for_existence": "1:AXIS1",
        "macros": {
            "MTRCTRL1": "01",
            "MTRCTRL2": "02",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        },
    },
]

TEST_MODES = [TestModes.DEVSIM]


class JawsMultigalilTests(JawsTestsBase, unittest.TestCase):
    """
    Tests for jaws split over multiple controllers
    """

    def setup_jaws(self):
        # 3 axes on one controller, one axis on the second controller
        self.MTR_NORTH = "MOT:MTR0101"
        self.MTR_SOUTH = "MOT:MTR0102"
        self.MTR_WEST = "MOT:MTR0103"
        self.MTR_EAST = "MOT:MTR0201"
        self.UNDERLYING_MTRS = OrderedDict([("N", self.MTR_NORTH),
                                            ("S", self.MTR_SOUTH),
                                            ("E", self.MTR_EAST),
                                            ("W", self.MTR_WEST)])
