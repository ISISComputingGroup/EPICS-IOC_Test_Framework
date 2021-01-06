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
ABORTS = ["Aborting X"]
QUENCHES = ["Quenched", ""]
READ_PVS = [
    {"PV": "STAT", "EXTRA_READ_PV":"STAT:RBV", "values":STATUSES, "init_value": ""},
    {"PV": "READY", "EXTRA_READ_PV":"READY:RBV", "values":READYS, "init_value":""},
    {"PV": "OUTPUT:FIELD:GAUSS", "EXTRA_READ_PV": "OUT:RBV", "values":GAUSS, "init_value":-4},
    {"PV": "OUTPUT:CURR", "EXTRA_READ_PV": "", "values":AMPSANDVOLTS, "init_value":-0.4},
    {"PV": "OUTPUT:VOLT", "EXTRA_READ_PV": "", "values":AMPSANDVOLTS, "init_value": -0.4},
    {"PV": "TARGET:TIME", "EXTRA_READ_PV": "", "values":TIMES, "init_value":""},
    {"PV": "QUENCH", "EXTRA_READ_PV": "", "values":QUENCHES, "init_value":""},
    #{"PV": "", "EXTRA_READ_PV": "", "values": "", "init_value":""},
]
WRITE_PVS = [
    {"PV": "TARGET", "EXTRA_READ_PV": "", "values": GAUSS, "init_value": -4},
]

class HifimagsTests(unittest.TestCase):
    """
    Tests for the Hifimags IOC.
    """
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    # RECSIM Tests

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

    @skip_if_recsim
    def test_GIVEN_readback_values_WHEN_sim_values_set_THEN_all_values_update(self):
        for PV in READ_PVS:
            if not PV["init_value"] == "":
                self.ca.set_pv_value("SIM:X:" + PV["PV"], PV["init_value"])
            for value in PV["values"]:
                sim_value = value
                self.ca.set_pv_value("SIM:X:" + PV["PV"], sim_value)
                self.ca.assert_that_pv_is("X:" + PV["PV"], sim_value)
                if not PV["EXTRA_READ_PV"] == "":
                    self.ca.assert_that_pv_is("X:" + PV["EXTRA_READ_PV"], sim_value)

    @skip_if_recsim
    def test_GIVEN_settable_values_WHEN_sim_values_set_THEN_all_values_update(self):
        for PV in WRITE_PVS:
            if not PV["init_value"] == "":
                self.ca.set_pv_value("X:" + PV["PV"] + ":SP", PV["init_value"])
            for value in PV["values"]:
                sim_value = value
                self.ca.set_pv_value("X:" + PV["PV"] + ":SP", sim_value)
                self.ca.assert_that_pv_is("SIM:X:" + PV["PV"], sim_value)
                if not PV["EXTRA_READ_PV"] == "":
                    self.ca.assert_that_pv_is("X:" + PV["EXTRA_READ_PV"], sim_value)

    @skip_if_recsim
    def test_GIVEN_error_active_WHEN_using_backwards_compatibility_THEN_the_correct_status_is_reported(self):
        sim_value = "There is a simulated error"
        self.ca.set_pv_value("SIM:X:STAT", sim_value)
        self.ca.set_pv_value("SIM:X:ERROR", "Error")
        self.ca.assert_that_pv_is("X:ERRORS:RBV", sim_value)
        self.ca.set_pv_value("SIM:X:ERROR", "No Error")
        self.ca.assert_that_pv_is("X:ERRORS:RBV", "")

    @skip_if_recsim
    def test_GIVEN_abort_requested_THEN_abort_is_propagated(self):
        sim_value = "Aborting X"
        self.ca.set_pv_value("X:ABORT:SP", 1)
        self.ca.assert_that_pv_is("SIM:X:ABORT", sim_value)

    def test_GIVEN_z_switching_is_needed_WHEN_the_ramp_rate_is_altered_THEN_it_should_be_propagated(self):
        sim_value = 1.546
        self.ca.set_pv_value("Z:RAMP:RATE:SP", sim_value)
        self.ca.assert_that_pv_is("Z:RAMP:RATE", sim_value)

    def test_GIVEN_z_switching_is_needed_WHEN_the_max_field_is_altered_THEN_it_should_be_propagated(self):
        sim_value = 20005
        self.ca.set_pv_value("Z:FIELD:MAX:SP", sim_value)
        self.ca.assert_that_pv_is("Z:FIELD:MAX", sim_value)
