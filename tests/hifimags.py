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
PERSISTS = ["Non Persisting", "Persisting"]
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
    {"MAG": "M", "PV": "RAMP:LEADS", "EXTRA_READ_PV": "", "values": LEADS, "init_value": ""},
    {"MAG": "M", "PV": "PERSIST", "EXTRA_READ_PV": "", "values": PERSISTS, "init_value": ""},
]
WRITE_SWITCH_PVS = [
    {"PV": "RAMP:RATE", "EXTRA_READ_PV": "", "values": SWITCHINGRAMPRATE, "init_value": ""},
    {"PV": "FIELD:MAX", "EXTRA_READ_PV": "", "values": SWITCHINGMAX, "init_value": ""},
    {"PV": "FIELD:MID", "EXTRA_READ_PV": "", "values": SWTICHINGMID, "init_value": ""},
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

    def setZeroes(self):
        for PSU in PSUS:
            self.ca.set_pv_value(PSU + ":ZERO", 0.2)
            self.ca.set_pv_value(PSU + ":ZEROFIELD", 0.3)


    def overrideDisables(self):
        for PSU in PSUS:
            self.ca.set_pv_value(PSU + ":DIS", 0)
        self.ca.set_pv_value("M:EXTRAS:DIS", 0)
        self.ca.set_pv_value("Z:SWITCH:DIS", 0)

    def checkMagnetsOff(self):
        self.ca.set_pv_value("MAGNETS:OFF:SP", "Off")
        for PSU in PSUS:
            self.ca.assert_that_pv_is(PSU + ":OUTPUT:FIELD:GAUSS", 0)
            self.ca.assert_that_pv_is(PSU + ":READY", "Ready")

    def setTarget(self, PSU, target):
        self.ca.set_pv_value(PSU + ":TARGET:SP", target)
        self.ca.set_pv_value(PSU + ":SET:SP", 1)

    def toggleRampLeads(self):
        self.ca.set_pv_value("M:RAMP:LEADS:SP", 1)
        self.ca.assert_that_pv_is("M:RAMP:LEADS", "Ramping")
        self.ca.set_pv_value("M:RAMP:LEADS:SP", 0)
        self.ca.assert_that_pv_is("M:RAMP:LEADS", "Not Ramping")

    def togglePersist(self):
        self.ca.set_pv_value("M:PERSIST:SP", 1)
        self.ca.assert_that_pv_is("M:PERSIST", "Persisting")
        self.ca.set_pv_value("M:PERSIST:SP", 0)
        self.ca.assert_that_pv_is("M:PERSIST", "Non Persisting")

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
        self.ca.set_pv_value("SIM:X:QUENCH", 0)

    def test_GIVEN_settable_values_WHEN_sim_values_set_THEN_all_values_update(self):
        self.overrideDisables()
        for PV in WRITE_PVS:
            if PV["init_value"] != "":
                self.ca.set_pv_value(PV["MAG"] + ":" + PV["PV"] + ":SP", PV["init_value"])
            for value in PV["values"]:
                sim_value = value
                self.ca.set_pv_value(PV["MAG"] + ":" + PV["PV"] + ":SP", sim_value)
                self.ca.assert_that_pv_is("SIM:" + PV["MAG"] + ":" + PV["PV"], sim_value)
                if not PV["EXTRA_READ_PV"] == "":
                    self.ca.assert_that_pv_is(PV["EXTRA_READ_PV"], sim_value)
        for PV in WRITE_SWITCH_PVS:
            if not PV["init_value"] == "":
                self.ca.set_pv_value("Z:" + PV["PV"] + ":SP", PV["init_value"])
            for value in PV["values"]:
                sim_value = value
                self.ca.set_pv_value("Z:" + PV["PV"] + ":SP", sim_value)
                self.ca.set_pv_value("Z:SWITCH:SET:SP", 1)
                self.ca.assert_that_pv_is("SIM:" + "Z:" + PV["PV"], sim_value)

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

    def test_GIVEN_abort_requested_THEN_abort_is_propagated(self):
        sim_value = "Aborting X"
        self.ca.set_pv_value("X:ABORT:SP", 1)
        self.ca.assert_that_pv_is("SIM:X:ABORT", sim_value)

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

    def test_GIVEN_active_temperature_sesnors_WHEN_sensor_is_updated_THEN_value_is_updated(self):
        for SENSOR in TEMPERATURE_SENSORS:
            self.ca.set_pv_value("SIM:TEMP:" + SENSOR, 2.5)
            for value in TEMPERATURES:
                sim_value = value
                self.ca.set_pv_value("SIM:TEMP:" + SENSOR, sim_value)
                self.ca.assert_that_pv_is("TEMP:" + SENSOR, sim_value)

    def test_GIVEN_all_magnets_on_WHEN_magnets_off_is_requested_THEN_all_magnets_are_ready_at_zero(self):
        self.overrideDisables()
        for PSU in PSUS:
            self.setTarget(PSU, 1)
            self.ca.assert_that_pv_is("SIM:" + PSU + ":SET:SP", "Ramping " + PSU)
            self.ca.assert_that_pv_is(PSU + ":OUTPUT:FIELD:GAUSS", 1)
        self.checkMagnetsOff()

    def test_WHEN_in_idle_mode_THEN_only_magnets_off_can_be_controlled(self):
        self.ca.set_pv_value("OPMODE:SP", 1)
        self.ca.set_pv_value("OPMODE:SP", 0)
        self.ca.assert_that_pv_is("OPMODE", "Idle")

        for PSU in PSUS:
            self.ca.assert_that_pv_is(PSU + ":DIS", PSU + " DISABLED")
            self.ca.assert_that_pv_is(PSU + ":TARGET:SP.DISP", "1")
            self.ca.assert_that_pv_is(PSU + ":SET:SP.DISP", "1")
            self.ca.set_pv_value("SIM:" + PSU + ":OUTPUT:FIELD:GAUSS", 2)
            self.ca.assert_that_pv_is("SIM:" + PSU + ":OUTPUT:FIELD:GAUSS", 2)

        for PV in WRITE_PVS:
            self.ca.assert_that_pv_is(PV["MAG"] + ":" + PV["PV"] + ":SP.DISP", "1")

        self.checkMagnetsOff()

    def test_WHEN_in_high_field_mode_THEN_only_main_and_z_can_be_controlled(self):
        self.setZeroes()
        self.overrideDisables()
        for PSU in PSUS:
            self.setTarget(PSU, 1)

        self.ca.set_pv_value("OPMODE:SP", 0)
        self.ca.set_pv_value("OPMODE:SP", 1)
        self.ca.assert_that_pv_is("OPMODE", "High Field")

        self.ca.assert_that_pv_is_number("X:OUTPUT:FIELD:GAUSS", 0.2, tolerance=1e-3)
        self.ca.assert_that_pv_is_number("Y:OUTPUT:FIELD:GAUSS", 0.2, tolerance=1e-3)
        self.ca.assert_that_pv_is_number("Z:OUTPUT:FIELD:GAUSS", 0.2, tolerance=1e-3)
        self.ca.assert_that_pv_is("M:OUTPUT:FIELD:GAUSS", 1)
        self.ca.assert_that_pv_is("X:DIS", "X DISABLED")
        self.ca.assert_that_pv_is("Y:DIS", "Y DISABLED")
        self.ca.assert_that_pv_is("Z:SWITCH:DIS", "Z DISABLED")
        self.ca.assert_that_pv_is("Z:DIS", "Z ENABLED")
        self.ca.assert_that_pv_is("M:DIS", "M ENABLED")
        self.ca.assert_that_pv_is("M:EXTRAS:DIS", "M ENABLED")

        self.setTarget("Z", 1.4)
        self.ca.assert_that_pv_is("Z:OUTPUT:FIELD:GAUSS", 1.4)

        self.setTarget("M", 3.4)
        self.ca.assert_that_pv_is("M:OUTPUT:FIELD:GAUSS", 3.4)

        self.toggleRampLeads()

        self.togglePersist()

        self.checkMagnetsOff()

    def test_WHEN_in_low_field_mode_THEN_x_y_z_and_m_extras_can_be_controlled(self):
        self.setZeroes()
        self.overrideDisables()
        for PSU in PSUS:
            self.setTarget(PSU, 1)

        self.ca.set_pv_value("OPMODE:SP", 0)
        self.ca.set_pv_value("OPMODE:SP", 2)
        self.ca.assert_that_pv_is("OPMODE", "Low Field")

        self.ca.assert_that_pv_is_number("X:OUTPUT:FIELD:GAUSS", 0.3, tolerance=1e-3)
        self.ca.assert_that_pv_is_number("Y:OUTPUT:FIELD:GAUSS", 0.3, tolerance=1e-3)
        self.ca.assert_that_pv_is_number("Z:OUTPUT:FIELD:GAUSS", 0.3, tolerance=1e-3)
        self.ca.assert_that_pv_is_number("M:OUTPUT:FIELD:GAUSS", 0.2, tolerance=1e-3)
        self.ca.assert_that_pv_is("M:PERSIST", "Non Persisting")
        self.ca.assert_that_pv_is("M:RAMP:LEADS", "Ramping")

        self.ca.assert_that_pv_is("X:DIS", "X ENABLED")
        self.ca.assert_that_pv_is("Y:DIS", "Y ENABLED")
        self.ca.assert_that_pv_is("Z:SWITCH:DIS", "Z DISABLED")
        self.ca.assert_that_pv_is("Z:DIS", "Z ENABLED")
        self.ca.assert_that_pv_is("M:DIS", "M DISABLED")
        self.ca.assert_that_pv_is("M:EXTRAS:DIS", "M ENABLED")

        self.setTarget("X", 1.4)
        self.ca.assert_that_pv_is("X:OUTPUT:FIELD:GAUSS", 1.4)

        self.setTarget("Y", 1.4)
        self.ca.assert_that_pv_is("Y:OUTPUT:FIELD:GAUSS", 1.4)

        self.setTarget("Z", 1.4)
        self.ca.assert_that_pv_is("Z:OUTPUT:FIELD:GAUSS", 1.4)

        self.toggleRampLeads()

        self.togglePersist()

        self.checkMagnetsOff()

    def test_WHEN_in_z_switching_mode_THEN_m_and_z_switch_can_be_controlled_with_sets_delayed(self):
        self.setZeroes()
        self.overrideDisables()
        for PSU in PSUS:
            self.setTarget(PSU, 1)

        self.ca.set_pv_value("OPMODE:SP", 0)
        self.ca.set_pv_value("OPMODE:SP", 3)
        self.ca.assert_that_pv_is("OPMODE", "Z Switching")

        self.ca.assert_that_pv_is_number("X:OUTPUT:FIELD:GAUSS", 0.2, tolerance=1e-3)
        self.ca.assert_that_pv_is_number("Y:OUTPUT:FIELD:GAUSS", 0.2, tolerance=1e-3)
        self.ca.assert_that_pv_is_number("Z:OUTPUT:FIELD:GAUSS", 1, tolerance=1e-3)
        self.ca.assert_that_pv_is_number("M:OUTPUT:FIELD:GAUSS", 1, tolerance=1e-3)

        self.ca.assert_that_pv_is("X:DIS", "X DISABLED")
        self.ca.assert_that_pv_is("Y:DIS", "Y DISABLED")
        self.ca.assert_that_pv_is("Z:SWITCH:DIS", "Z ENABLED")
        self.ca.assert_that_pv_is("Z:DIS", "Z DISABLED")
        self.ca.assert_that_pv_is("M:DIS", "M ENABLED")
        self.ca.assert_that_pv_is("M:EXTRAS:DIS", "M ENABLED")

        self.ca.set_pv_value("Z:RAMP:RATE:SP", 0.563)
        self.ca.set_pv_value("Z:FIELD:MAX:SP", 2.4)
        self.ca.set_pv_value("Z:FIELD:MID:SP", 1.45)

        self.ca.set_pv_value("Z:SWITCH:SET:SP", 1)

        self.ca.assert_that_pv_is_number("Z:RAMP:RATE", 0.563, tolerance=1e-3)
        self.ca.assert_that_pv_is_number("Z:FIELD:MAX", 2.4, tolerance=1e-3)
        self.ca.assert_that_pv_is_number("Z:FIELD:MID", 1.45, tolerance=1e-3)

        self.setTarget("M", -1.4)
        self.ca.assert_that_pv_is("M:OUTPUT:FIELD:GAUSS", -1.4)

        self.toggleRampLeads()

        self.togglePersist()

        self.checkMagnetsOff()

    def test_WHEN_a_magnet_sees_a_quench_THEN_system_goes_into_idle_mode(self):
        self.ca.set_pv_value("OPMODE:SP", 2)
        self.ca.assert_that_pv_is("OPMODE", "Low Field")
        self.ca.set_pv_value("SIM:M:QUENCH", 1)
        self.ca.assert_that_pv_is("M:QUENCH", "Quenched")
        self.ca.assert_that_pv_is("OPMODE", "Idle")
        self.ca.set_pv_value("SIM:M:QUENCH", 0)
