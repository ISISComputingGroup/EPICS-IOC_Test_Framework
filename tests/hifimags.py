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

PSUS = ["X","Y","Z","M"]

STATUSES = ["Unit Test"]
READYS = ["Ready", "Not Ready"]
GAUSS = [0,10,-10,50.4,2164.5657,0,-0.57,-36425.434]
AMPSANDVOLTS = [0,1,-1,0.435,1.1,0,-0.3687,-0.97]
TIMES = ["11:24:32"]
ABORTS = ["Aborting X"]
QUENCHES = ["Quenched", ""]
SWITCHINGRAMPRATE = [1.546]
SWITCHINGMAX = [20005]
SWTICHINGMID = [523.8]
LEADS = ["Not Ramping", "Ramping"]
PERSISTS = ["Non persisting", "Persisting"]
OPMODES = ["Idle", "High Field", "Low Field", "Z Switching"]
HALLS = [0,12.456,-0.45,20113.89]
COMP_TEXTS = ["Compressor Error", ""]
ERRORS = ["No Error", "Error"]
ONOFF = ["Off", "On"]
TEMPERATURES = [0,5.681,856.187,191.3]
TEMPERATURE_SENSORS = ["STAGE1", "SHIELD", "SWITCH", "STAGE2A", "STAGE2B", "INRABAS"]
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
    {"MAG": "X", "PV": "TARGET", "EXTRA_READ_PV": "", "values": GAUSS, "init_value": -4},
    {"MAG": "Z", "PV": "RAMP:RATE", "EXTRA_READ_PV": "", "values": SWITCHINGRAMPRATE, "init_value": ""},
    {"MAG": "Z", "PV": "FIELD:MAX", "EXTRA_READ_PV": "", "values": SWITCHINGMAX, "init_value": ""},
    {"MAG": "Z", "PV": "FIELD:MID", "EXTRA_READ_PV": "", "values": SWTICHINGMID, "init_value": ""},
    {"MAG": "M", "PV": "RAMP:LEADS", "EXTRA_READ_PV": "", "values": LEADS, "init_value": ""},
    {"MAG": "M", "PV": "PERSIST", "EXTRA_READ_PV": "", "values": PERSISTS, "init_value": ""},
]
MAIN_PVS = [
    {"PV": "STAT", "EXTRA_READ_PV":"MAIN:STAT:RBV", "values":STATUSES, "init_value": ""},
    {"PV": "READY", "EXTRA_READ_PV": "MAIN:READY:RBV", "values": READYS, "init_value": ""},
    {"PV": "OUTPUT:FIELD:GAUSS", "EXTRA_READ_PV": "MAIN:OUT:RBV", "values":GAUSS, "init_value":-4},
    {"PV": "TARGET:TIME", "EXTRA_READ_PV": "MAIN:MINTO:RBV", "values":TIMES, "init_value":""},
    {"PV": "OUTPUT:FIELD:PERSIST:GAUSS", "EXTRA_READ_PV": "", "values":GAUSS, "init_value":""},
]
SYS_READ_PVS = [
    {"PV": "HALL:SENS1", "EXTRA_READ_PV": "HALL:SENS1:RBV", "values": HALLS, "init_value": -1},
    {"PV": "HALL:SENS2", "EXTRA_READ_PV": "HALL:SENS2:RBV", "values": HALLS, "init_value": -1},
    {"PV": "COMP:R:ERROR:TEXT:RBV", "EXTRA_READ_PV": "", "values": COMP_TEXTS, "init_value": "Testing"},
    {"PV": "COMP:L:ERROR:TEXT:RBV", "EXTRA_READ_PV": "", "values": COMP_TEXTS, "init_value": "Testing"},
    {"PV": "COMP:R:ERROR:STAT:RBV", "EXTRA_READ_PV": "", "values": ERRORS, "init_value": "Error"},
    {"PV": "COMP:L:ERROR:STAT:RBV", "EXTRA_READ_PV": "", "values": ERRORS, "init_value": "Error"},
    {"PV": "COMP:R:ON:RBV", "EXTRA_READ_PV": "", "values": ONOFF, "init_value": "On"},
    {"PV": "COMP:L:ON:RBV", "EXTRA_READ_PV": "", "values": ONOFF, "init_value": "On"},
]
SYS_WRITE_PVS = [
    {"PV": "OPMODE", "EXTRA_READ_PV": "OPMODE:RBV", "values": OPMODES, "init_value": "High Field"},
]

class HifimagsTests(unittest.TestCase):
    """
    Tests for the Hifimags IOC.
    """
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def overrideDisables(self):
        for PSU in PSUS:
            self.ca.set_pv_value(PSU + ":DIS", 0)
        self.ca.set_pv_value("M:EXTRAS:DIS", 0)
        self.ca.set_pv_value("Z:SWITCH:DIS", 0)

    # RECSIM Tests

    #@skip_if_recsim
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

    #@skip_if_recsim
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

    #@skip_if_recsim
    def test_GIVEN_settable_values_WHEN_sim_values_set_THEN_all_values_update(self):
        self.overrideDisables()
        for PV in WRITE_PVS:
            if not PV["init_value"] == "":
                self.ca.set_pv_value(PV["MAG"] + ":" + PV["PV"] + ":SP", PV["init_value"])
            for value in PV["values"]:
                sim_value = value
                self.ca.set_pv_value(PV["MAG"] + ":" + PV["PV"] + ":SP", sim_value)
                self.ca.assert_that_pv_is("SIM:" + PV["MAG"] + ":" + PV["PV"], sim_value)
                if not PV["EXTRA_READ_PV"] == "":
                    self.ca.assert_that_pv_is(PV["EXTRA_READ_PV"], sim_value)

    #@skip_if_recsim
    def test_GIVEN_error_active_WHEN_using_backwards_compatibility_THEN_the_correct_status_is_reported(self):
        # Errors for Main PSU different, so use M rather than X
        sim_value = "There is a simulated error"
        self.ca.set_pv_value("SIM:M:STAT", sim_value)
        self.ca.set_pv_value("SIM:M:ERROR", "Error")
        self.ca.assert_that_pv_is("M:ERRORS:RBV", sim_value)
        self.ca.assert_that_pv_is("MAIN:ERRORS:RBV", sim_value)
        self.ca.set_pv_value("SIM:M:ERROR", "No Error")
        self.ca.assert_that_pv_is("M:ERRORS:RBV", "")
        self.ca.assert_that_pv_is("MAIN:ERRORS:RBV", "")

    #@skip_if_recsim
    def test_GIVEN_abort_requested_THEN_abort_is_propagated(self):
        sim_value = "Aborting X"
        self.ca.set_pv_value("X:ABORT:SP", 1)
        self.ca.assert_that_pv_is("SIM:X:ABORT", sim_value)

    #@skip_if_recsim
    def test_GIVEN_readback_values_WHEN_sim_main_values_set_THEN_all_values_update(self):
        for PV in MAIN_PVS:
            if not PV["init_value"] == "":
                self.ca.set_pv_value("SIM:M:" + PV["PV"], PV["init_value"])
            for value in PV["values"]:
                sim_value = value
                self.ca.set_pv_value("SIM:M:" + PV["PV"], sim_value)
                self.ca.assert_that_pv_is("M:" + PV["PV"], sim_value)
                if not PV["EXTRA_READ_PV"] == "":
                    self.ca.assert_that_pv_is(PV["EXTRA_READ_PV"], sim_value)

    #@skip_if_recsim
    def test_GIVEN_readback_values_WHEN_system_values_set_THEN_all_values_update(self):
        for PV in SYS_READ_PVS:
            if not PV["init_value"] == "":
                self.ca.set_pv_value("SIM:" + PV["PV"], PV["init_value"])
            for value in PV["values"]:
                sim_value = value
                self.ca.set_pv_value("SIM:" + PV["PV"], sim_value)
                self.ca.assert_that_pv_is(PV["PV"], sim_value)
                if not PV["EXTRA_READ_PV"] == "":
                    self.ca.assert_that_pv_is(PV["EXTRA_READ_PV"], sim_value)

    #@skip_if_recsim
    def test_GIVEN_settable_values_WHEN_system_values_set_THEN_all_values_update(self):
        for PV in SYS_WRITE_PVS:
            if not PV["init_value"] == "":
                self.ca.set_pv_value(PV["PV"] + ":SP", PV["init_value"])
            for value in PV["values"]:
                sim_value = value
                self.ca.set_pv_value(PV["PV"] + ":SP", sim_value)
                self.ca.assert_that_pv_is("SIM:" + PV["PV"], sim_value)
                if not PV["EXTRA_READ_PV"] == "":
                    self.ca.assert_that_pv_is(PV["EXTRA_READ_PV"], sim_value)

    #@skip_if_recsim
    def test_GIVEN_active_temperature_sesnors_WHEN_sensor_is_updated_THEN_value_is_updated(self):
        for SENSOR in TEMPERATURE_SENSORS:
            self.ca.set_pv_value("SIM:TEMP:" + SENSOR, 2.5)
            for value in TEMPERATURES:
                sim_value = value
                self.ca.set_pv_value("SIM:TEMP:" + SENSOR, sim_value)
                self.ca.assert_that_pv_is("TEMP:" + SENSOR, sim_value)

    #@skip_if_recsim
    def test_GIVEN_all_magnets_on_WHEN_magnets_off_is_requested_THEN_all_magnets_are_ready_at_zero(self):
        self.overrideDisables()
        for PSU in PSUS:
            self.ca.set_pv_value(PSU + ":TARGET:SP", 1)
            self.ca.set_pv_value(PSU + ":SET:SP", 1)
            self.ca.assert_that_pv_is("SIM:" + PSU + ":SET:SP", "Ramping " + PSU)
            self.ca.assert_that_pv_is(PSU + ":OUTPUT:FIELD:GAUSS", 1)
        self.ca.set_pv_value("MAGNETS:OFF:SP", "Off")
        for PSU in PSUS:
            self.ca.assert_that_pv_is(PSU + ":OUTPUT:FIELD:GAUSS", 0)
            self.ca.assert_that_pv_is(PSU + ":READY", "Ready")

    #@skip_if_recsim
    def test_WHEN_in_idle_mode_THEN_only_magnets_off_can_be_controlled(self):
        self.ca.set_pv_value("OPMODE:SP", 1)
        self.ca.set_pv_value("OPMODE:SP", 0)
        self.ca.assert_that_pv_is("OPMODE", "Idle")
        # Verify that all the disable controls are True
        # Verify that each target cannot be set, and that all other controls are inoperative except Magnets Off

        for PSU in PSUS:
            self.ca.assert_that_pv_is(PSU + ":DIS", PSU + " DISABLED")
            self.ca.assert_that_pv_is(PSU + ":TARGET:SP.DISP", "1")
            self.ca.assert_that_pv_is(PSU + ":SET:SP.DISP", "1")
            self.ca.set_pv_value("SIM:" + PSU + ":OUTPUT:FIELD:GAUSS", 2)
            self.ca.assert_that_pv_is("SIM:" + PSU + ":OUTPUT:FIELD:GAUSS", 2)

        for PV in WRITE_PVS:
            self.ca.assert_that_pv_is(PV["MAG"] + ":" + PV["PV"] + ":SP.DISP", "1")

        self.ca.set_pv_value("MAGNETS:OFF:SP", "Off")
        for PSU in PSUS:
            self.ca.assert_that_pv_is(PSU + ":OUTPUT:FIELD:GAUSS", 0)
            self.ca.assert_that_pv_is(PSU + ":READY", "Ready")


