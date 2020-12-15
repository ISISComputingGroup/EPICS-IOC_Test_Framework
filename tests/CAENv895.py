from __future__ import division

import os
import unittest
import shutil
import time
from contextlib import contextmanager

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir

from utils.test_modes import TestModes
from utils.ioc_launcher import IOCRegister

AUTOSAVE_DIR = os.path.join("C:/", "Instrument", "var", "autosave", "CAENV895_01")

DEVICE_PREFIX = "CAENV895_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("CAENV895"),
        "pv_for_existence": "CR0:BOARD_ID",
    },
]

TEST_MODES = [TestModes.DEVSIM]

class CAENv895Tests(unittest.TestCase):
    """
    Tests for CAENv895
    """
    
    def setUp(self):
        try:
            os.makedirs(AUTOSAVE_DIR)
        except:
            pass # use exist_ok=True when we can
        shutil.copyfile("test_data/caenv895/vmeconfig_defaults.cfg", os.path.join(AUTOSAVE_DIR,"vmeconfig_defaults.cfg"))
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("CR0:BOARD_ID")

    def test_GIVEN_ioc_WHEN_startup_complet_THEN_initial_values_ok(self):
        self.ca.assert_that_pv_is("CR0:CRATE", 0)
        self.ca.assert_that_pv_is("CR0:BOARD_ID", 0)
    
    def test_GIVEN_output_widths_WHEN_output_widths_set_THEN_width_read_back(self):
        # GIVEN
        width_0_to_7 = 10
        width_8_to_15 = 13
        # WHEN
        self.ca.set_pv_value("CR0:C0:OUT:WIDTH:0_TO_7:SP", width_0_to_7)
        self.ca.set_pv_value("CR0:C0:OUT:WIDTH:8_TO_15:SP", width_8_to_15)
        # THEN
        self.ca.assert_that_pv_is("SIM:CR0:C0:OUT:WIDTH:0_TO_7", width_0_to_7)
        self.ca.assert_that_pv_is("SIM:CR0:C0:OUT:WIDTH:8_TO_15", width_8_to_15)
