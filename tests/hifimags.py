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
        "macros": {"X_IOC": "NA", "Y_IOC": "NA", "Z_IOC": "NA"},
        # "pv_for_existence": "",
    },
]

TEST_MODES = [TestModes.RECSIM]

PSUS = ["X","Y","Z"]

STATUSES = ["Unit Test"]
READYS = ["Ready", "Not Ready"]
GAUSS = [0,10,-10,50.4,2164.5657,0,-0.57,-36425.434]
AMPSANDVOLTS = [0,1,-1,0.435,1.1,0,-0.3687,-0.97]
TIMES = ["11:24:32"]
PVS = [
    {"PV": "STAT", "EXTRA_READ_PV":"STAT:RBV", "values":STATUSES, "init_value": ""},
    {"PV": "READY", "EXTRA_READ_PV":"READY:RBV", "values":READYS, "init_value":""},
    {"PV": "OUTPUT:FIELD:GAUSS", "EXTRA_READ_PV": "OUT:RBV", "values":GAUSS, "init_value":-4},
    {"PV": "OUTPUT:CURR", "EXTRA_READ_PV": "", "values":AMPSANDVOLTS, "init_value":-0.4},
    {"PV": "OUTPUT:VOLT", "EXTRA_READ_PV": "", "values":AMPSANDVOLTS, "init_value": -0.4},
    {"PV": "TARGET:TIME", "EXTRA_READ_PV": "", "values":TIMES, "init_value":""},
    #{"PV": "", "EXTRA_READ_PV": "", "values": "", "init_value":""},
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

    def test_GIVEN_updated_source_values_in_arrays_WHEN_sim_values_set_THEN_all_values_update(self):
        for PV in PVS:
            if not PV["init_value"] == "":
                self.ca.set_pv_value("SIM:X:" + PV["PV"], PV["init_value"])
            for value in PV["values"]:
                sim_value = value
                self.ca.set_pv_value("SIM:X:" + PV["PV"], sim_value)
                self.ca.assert_that_pv_is("X:" + PV["PV"], sim_value)
                if not PV["EXTRA_READ_PV"] == "":
                    self.ca.assert_that_pv_is("X:" + PV["EXTRA_READ_PV"], sim_value)

    # Skipping as errors are currently not propagating, and continuing with other items would be beneficial
    def test_GIVEN_error_active_THEN_correct_status_reported(self):
        sim_value = "There is a simulated error"
        self.ca.set_pv_value("SIM:X:STAT", sim_value)
        self.ca.set_pv_value("SIM:X:ERROR", "Error")
        self.ca.assert_that_pv_is("X:ERRORS:RBV", sim_value)
        self.ca.set_pv_value("SIM:X:ERROR", "No Error")
        self.ca.assert_that_pv_is("X:ERRORS:RBV", "")