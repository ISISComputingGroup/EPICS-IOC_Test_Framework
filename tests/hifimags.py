import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "HIFIMAGS_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HIFIMAGS"),
        "macros": {},
        # "pv_for_existence": "",
    },
]


TEST_MODES = [TestModes.RECSIM]

PSUS = ["X","Y","Z"]
PVS = [
    {"PV": "STAT", "EXTRA_READ_PV":"STAT:RBV", "value":"Unit Test", "init_value":""},
    {"PV": "READY", "EXTRA_READ_PV":"READY:RBV", "value":"Ready", "init_value":""},
    {"PV": "READY", "EXTRA_READ_PV":"READY:RBV", "value":"Not Ready", "init_value":1}
]

class HifimagsTests(unittest.TestCase):
    """
    Tests for the Hifimags IOC.
    """
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_sim_status_WHEN_sim_status_is_updated_THEN_all_statuses_match(self):
        sim_status = "Unit Test"
        for PSU in PSUS:
            self.ca.set_pv_value("SIM:" + PSU + ":STAT", sim_status)
            self.ca.assert_that_pv_is(PSU + ":STAT:RBV", sim_status)
            self.ca.assert_that_pv_is(PSU + ":STAT", sim_status)
        sim_status = ""
        for PSU in PSUS:
            self.ca.set_pv_value("SIM:" + PSU + ":STAT", sim_status)
            self.ca.assert_that_pv_is(PSU + ":STAT:RBV", sim_status)
            self.ca.assert_that_pv_is(PSU + ":STAT", sim_status)

    def test_GIVEN_backward_compatibilty_WHEN_sim_values_set_THEN_all_values_update(self):
        for PV in PVS:
            if not PV["init_value"] == "":
                self.ca.set_pv_value("SIM:X:" + PV["PV"], PV["init_value"])
            sim_value = PV["value"]
            self.ca.set_pv_value("SIM:X:" + PV["PV"], sim_value)
            self.ca.assert_that_pv_is("X:" + PV["PV"], sim_value)
            if not PV["EXTRA_READ_PV"] == "":
                self.ca.assert_that_pv_is("X:" + PV["EXTRA_READ_PV"], sim_value)

    def test_GIVEN_error_active_THEN_correct_status_reported(self):
        sim_value = "There is a simulated error"
        self.ca.set_pv_value("SIM:X:STAT", sim_value)
        self.ca.set_pv_value("SIM:X:ERROR", "Error")
        self.ca.assert_that_pv_is("X:ERRORS:RBV", sim_value)
        self.ca.set_pv_value("SIM:X:ERROR", "No Error")
        self.ca.assert_that_pv_is("X:ERRORS:RBV", "")