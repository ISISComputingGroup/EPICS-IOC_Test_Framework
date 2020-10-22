import contextlib
import shutil
import unittest
import os

import six
from lxml import etree
import copy

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list
from parameterized import parameterized

MTR_01 = "GALIL_01"

test_path = os.path.realpath(
    os.path.join(os.getenv("EPICS_KIT_ROOT"), "support", "sampleChanger", "master", "settings", "sans_sample_changer"))

AXES = ["SC:X", "SC:Y"]

IOCS = [
    {
        "name": MTR_01,
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "MTR0101",
        "custom_prefix": "MOT",
        "macros": {
            "MTRCTRL": "01",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        },
    },
]

TEST_MODES = [TestModes.DEVSIM]

SLOTS = ["B", "CB", "CT", "GT", "T", "WB", "WT"]


class SampleChangerTests(unittest.TestCase):
    """
    Tests for the sample changer.
    """
    def setUp(self):
        self.ca = ChannelAccess(default_timeout=5)

        self.ca.assert_that_pv_exists("SAMPCHNG:SLOT")
        for axis in AXES:
            self.ca.assert_that_pv_exists("MOT:{}".format(axis))

    @parameterized.expand(parameterized_list([
        {
            "slot_name": "_ALL",
            "positions_exist": ["{}CB".format(n) for n in range(1, 14+1)] + ["{}CT".format(n) for n in range(1, 14+1)],
            "positions_not_exist": [],
        },
        {
            "slot_name": "CT",
            "positions_exist": ["{}CT".format(n) for n in range(1, 14+1)],
            "positions_not_exist": ["{}CB".format(n) for n in range(1, 14+1)],
        },
        {
            "slot_name": "CB",
            "positions_exist": ["{}CB".format(n) for n in range(1, 14+1)],
            "positions_not_exist": ["{}CT".format(n) for n in range(1, 14+1)],
        },
    ]))
    def test_WHEN_slot_set_to_empty_string_THEN_all_positions_listed(self, _, settings):

        self.ca.assert_setting_setpoint_sets_readback(readback_pv="SAMPCHNG:SLOT", value=settings["slot_name"])

        for pos in settings["positions_exist"]:
            self.ca.assert_that_pv_value_causes_func_to_return_true("LKUP:SAMPLE:POSITIONS",
                                                                    func=lambda val: pos in val)

        for pos in settings["positions_not_exist"]:
            self.ca.assert_that_pv_value_causes_func_to_return_true("LKUP:SAMPLE:POSITIONS",
                                                                    func=lambda val: pos not in val)

    def test_WHEN_invalid_slot_is_entered_THEN_old_slot_kept(self):
        # First set a valid slot
        self.ca.assert_setting_setpoint_sets_readback(readback_pv="SAMPCHNG:SLOT", value="CT")

        self.ca.set_pv_value("SAMPCHNG:SLOT:SP", "does_not_exist", sleep_after_set=0)
        self.ca.assert_that_pv_alarm_is("SAMPCHNG:SLOT:SP", self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_is("SAMPCHNG:SLOT", "CT")
        self.ca.assert_that_pv_value_is_unchanged("SAMPCHNG:SLOT", wait=3)

        for pos in ["{}CT".format(n) for n in range(1, 14+1)]:
            self.ca.assert_that_pv_value_causes_func_to_return_true("LKUP:SAMPLE:POSITIONS",
                                                                    func=lambda val: pos in val)

    def test_available_slots_can_be_loaded(self):
        self.ca.assert_that_pv_value_causes_func_to_return_true("SAMPCHNG:AVAILABLE_SLOTS",
                                                                func=lambda val: all(s in val for s in SLOTS))

    @contextlib.contextmanager
    def _temporarily_add_slot(self, new_slot_name):

        file_paths = [os.path.join(test_path, "samplechanger.xml"), os.path.join(test_path, "rack_definitions.xml")]
        xml_trees = {}

        for file_path in file_paths:
            xml_trees[file_path] = etree.parse(file_path)
            shutil.copy2(file_path, file_path + ".backup")

        try:
            for path, tree in xml_trees.iteritems():
                slot = tree.find("//slot")
                new_slot = copy.deepcopy(slot)
                new_slot.set("name", new_slot_name)
                slot.getparent().insert(0, new_slot)

                tree.write(path)

            yield

        finally:
            for file_path in file_paths:
                os.remove(file_path)
                shutil.move(file_path + ".backup", file_path)

    def new_slot_positions_exist(self, new_slot_name):
        def _wrapper(val):
            # Prefixes for positions are either numeric (e.g. 1) or alphabetic (e.g. A)
            return any(prefix + new_slot_name in val for prefix in ["A", "1"])
        return _wrapper

    def new_slot_positions_do_not_exist(self, new_slot_name):
        def _wrapper(val):
            # Prefixes for positions are either numeric (e.g. 1) or alphabetic (e.g. A)
            return all(prefix + new_slot_name not in val for prefix in ["A", "1"])
        return _wrapper

    def test_GIVEN_sample_changer_file_modified_THEN_new_changer_available(self):
        new_slot_name = "NEWSLOT"
        with self._temporarily_add_slot(new_slot_name):
            # assert new slot has been picked up
            self.ca.assert_that_pv_value_causes_func_to_return_true("SAMPCHNG:AVAILABLE_SLOTS",
                                                                    func=lambda val: new_slot_name in val)

        self.ca.assert_that_pv_value_causes_func_to_return_true("SAMPCHNG:AVAILABLE_SLOTS",
                                                                func=lambda val: new_slot_name not in val)

    def test_GIVEN_sample_changer_file_modified_THEN_new_positions_available(self):
        new_slot_name = "NEWSLOT"
        with self._temporarily_add_slot(new_slot_name):
            # assert new slot has been picked up
            self.ca.assert_that_pv_value_causes_func_to_return_true("SAMPCHNG:AVAILABLE_SLOTS",
                                                                    func=lambda val: new_slot_name in val)

            # Select newly added sample changer
            self.ca.set_pv_value("SAMPCHNG:SLOT:SP", new_slot_name)

            # Assert positions from newly added sample changer exist
            # Position names are slot_name + either 1 or A depending on naming convention of slot
            self.ca.assert_that_pv_value_causes_func_to_return_true("LKUP:SAMPLE:POSITIONS",
                                                                    func=self.new_slot_positions_exist(new_slot_name))

        # Now out of context manager, NEWSLOT no longer exists
        self.ca.assert_that_pv_value_causes_func_to_return_true("SAMPCHNG:AVAILABLE_SLOTS",
                                                                func=lambda val: new_slot_name not in val)

        # Use all positions from all available changers
        self.ca.set_pv_value("SAMPCHNG:SLOT:SP", "_ALL")

        # Positions from the now-deleted changer shouldn't exist
        self.ca.assert_that_pv_value_causes_func_to_return_true("LKUP:SAMPLE:POSITIONS",
                                                                func=self.new_slot_positions_do_not_exist(new_slot_name))
