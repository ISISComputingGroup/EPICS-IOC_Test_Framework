import itertools
import os
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim, skip_if_devsim

# Device prefix
DEVICE_PREFIX = "FINS_01"

IOC_NAME = "FINS"
TEST_PATH = os.path.join(EPICS_TOP, "ioc", "master", IOC_NAME, "exampleSettings", "HELIUM_RECOVERY")

IOC_PREFIX = "{}:HE_RCVRY".format(DEVICE_PREFIX)

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("FINS"),
        "custom_prefix": IOC_PREFIX,
        "macros": {
            "FINSCONFIGDIR": TEST_PATH.replace("\\", "/"),
            "PLC_IP": "127.0.0.1",
            "PLC_NODE": 58,
        },
        "emulator": "fins",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

PV_NAMES = ["HEARTBEAT", "MCP:BANK1:TS2", "MCP:BANK1:TS1", "MCP1:BANK2:IMPURE_HE", "MCP2:BANK2:IMPURE_HE",
            "MCP1:BANK3:MAIN_HE_STORAGE", "MCP2:BANK3:MAIN_HE_STORAGE", "MCP1:BANK4:DLS_HE_STORAGE",
            "MCP2:BANK4:DLS_HE_STORAGE", "MCP1:BANK5:SPARE_STORAGE", "MCP2:BANK5:SPARE_STORAGE",
            "MCP1:BANK6:SPARE_STORAGE", "MCP2:BANK6:SPARE_STORAGE", "MCP1:BANK7:SPARE_STORAGE",
            "MCP2:BANK7:SPARE_STORAGE", "MCP1:BANK8:SPARE_STORAGE", "MCP2:BANK8:SPARE_STORAGE", "MCP:INLET:PRESSURE",
            "MCP:EXTERNAL_TEMP", "GAS_LIQUEFACTION:MASS_FLOW", "HE_FILLS:MASS_FLOW", "CMPRSSR:INTERNAL_TEMP",
            "COLDBOX:HE_TEMP", "COLDBOX:HE_TEMP:LIMIT", "TRANSPORT_DEWAR:PRESSURE", "HE_PURITY", "DEW_POINT",
            "FLOW_METER:TS2:EAST", "TS2:EAST:O2", "FLOW_METER:TS2:WEST", "TS2:WEST:O2", "TS1:NORTH:O2", "TS1:SOUTH:O2",
            "FLOW_METER:TS1:WINDOW", "FLOW_METER:TS1:SHUTTER", "FLOW_METER:TS1:VOID", "GC:R108:U40",
            "GC:R108:DEWAR_FARM", "GC:R55:TOTAL", "GC:R55:NORTH", "GC:R55:SOUTH", "GC:MICE_HALL", "GC:MUON",
            "GC:PEARL_HRPD_MARI_ENGINX", "GC:SXD_AND_MERLIN", "GC:CRYO_LAB", "GC:MAPS_AND_VESUVIO", "GC:SANDALS",
            "GC:CRISP_AND_LOQ", "GC:IRIS_AND_OSIRIS", "GC:INES", "GC:RIKEN", "GC:R80:TOTAL", "GC:R53", "GC:R80:EAST",
            "GC:WISH", "GC:WISH:DEWAR_FARM", "GC:LARMOR_AND_OFFSPEC", "GC:ZOOM_SANS2D_AND_POLREF", "GC:MAGNET_LAB",
            "GC:IMAT", "GC:LET_AND_NIMROD", "GC:R80:WEST", "COLDBOX:MV108", "BANK1:TS2:RSPPL:AVG_PURITY",
            "BANK1:TS1:RSPPL:AVG_PURITY", "BANK2:IMPURE_HE:AVG_PURITY", "BANK3:MAIN_STRG:AVG_PURITY",
            "BANK4:DLS_STRG:AVG_PURITY", "BANK5:SPR_STRG:AVG_PURITY", "BANK6:SPR_STRG:AVG_PURITY",
            "BANK7:SPR_STRG:AVG_PURITY", "BANK8:SPR_STRG:AVG_PURITY", "COLDBOX:TURBINE_100:SPEED",
            "COLDBOX:TURBINE_101:SPEED", "COLDBOX:T106:TEMP", "COLDBOX:TT111:TEMP", "COLDBOX:PT102:PRESSURE",
            "BUFFER:PT203:PRESSURE", "PURIFIER:TT104:TEMP", "PURIFIER:TT102:TEMP", "COLDBOX:TT108:TEMP",
            "COLDBOX:PT112:PRESSURE", "COLDBOX:CNTRL_VALVE_103", "COLDBOX:CNTRL_VALVE_111", "COLDBOX:CNTRL_VALVE_112",
            "MOTHER_DEWAR:HE_LEVEL", "PURIFIER:LEVEL", "IMPURE_HE_SUPPLY:PRESSURE", "CMPRSSR:LOW_CNTRL_PRESSURE",
            "CMPRSSR:HIGH_CNTRL_PRESSURE", "CNTRL_VALVE_2250", "CNTRL_VALVE_2150", "CNTRL_VALVE_2160",
            "LIQUID_NITROGEN:STATUS", "MCP:LIQUID_HE_INVENTORY"]

TEST_VALUES = range(1, len(PV_NAMES) + 1)

# list of names for the ai records. It is a separate list as we want to test floating point values with these PVs
ANALOGUE_IN_PV_NAMES = ["MASS_FLOW:HE_RSPPL:TS2:EAST", "MASS_FLOW:HE_RSPPL:TS2:WEST", "MASS_FLOW:HE_RSPPL:TS1:VOID",
                        "MASS_FLOW:HE_RSPPL:TS1:WNDW", "MASS_FLOW:HE_RSPPL:TS1:SHTR"]

FLOAT_TEST_VALUES = [i + float(i) / 10 for i in range(1, len(ANALOGUE_IN_PV_NAMES) + 1)]

AUTO_MANUAL_PV_NAMES = ["CNTRL_VALVE_120:MODE", "CNTRL_VALVE_121:MODE", "LOW_PRESSURE:MODE", "HIGH_PRESSURE:MODE",
                        "TIC106:MODE", "PIC112:MODE"]

CONTROL_VALVE_POSITION_VALUES = ["Opening", "Closing", "No movement"]

PURIFIER_STATUS_VALUES = ["OFF", "FLUSHING", "COOLDOWN 1", "COOLDOWN 2", "CLEANING MODE", "REGENERATION", "STANDBY"]

COMPRESSOR_STATUS_VALUES = ["NOT READY TO START", "READY TO START", "RUNNING"]

COLDBOX_STATUS_VALUES = ["IN COOLDOWN", "RUNNING", "NOT RUNNING"]

VALVE_STATUS_PVS = ["CNTRL_VALVE_112:STATUS", "CNTRL_VALVE_2150:STATUS", "CNTRL_VALVE_2160:STATUS",
                    "CNTRL_VALVE_2250:STATUS", "MOTORISED_VALVE_110:STATUS", "MOTORISED_VALVE_160:STATUS",
                    "MOTORISED_VALVE_163:STATUS", "MOTORISED_VALVE_167:STATUS", "MOTORISED_VALVE_172:STATUS",
                    "MOTORISED_VALVE_174:STATUS", "MOTORISED_VALVE_175:STATUS", "MOTORISED_VALVE_176:STATUS",
                    "MOTORISED_VALVE_177:STATUS", "MOTORISED_VALVE_178:STATUS", "CNTRL_VALVE_103:STATUS",
                    "CNTRL_VALVE_111:STATUS"]

VALVE_STATUS_VALUES = ["OPENING", "SWEEPING", "CLOSED", "FAULT"]


class HeliumRecoveryPLCTests(unittest.TestCase):
    """
    Tests for the FINS helium gas recovery PLC IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(IOCS[0]["emulator"], DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=20, device_prefix=IOC_PREFIX)

        if not IOCRegister.uses_rec_sim:
            self._lewis.backdoor_run_function_on_device("reset")
            self._lewis.backdoor_set_on_device("connected", True)

    @parameterized.expand(parameterized_list(zip(PV_NAMES, TEST_VALUES)))
    @skip_if_recsim("lewis backdoor not supported in recsim")
    def test_WHEN_value_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, test_value))
        self.ca.assert_that_pv_is(pv_name, test_value, timeout=40)

    @parameterized.expand(parameterized_list(zip(PV_NAMES, TEST_VALUES)))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_value_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self.ca.set_pv_value("SIM:{}".format(pv_name), test_value)
        self.ca.assert_that_pv_is(pv_name, test_value, timeout=40)

    @parameterized.expand(parameterized_list(zip(ANALOGUE_IN_PV_NAMES, FLOAT_TEST_VALUES)))
    @skip_if_recsim("lewis backdoor not supported in recsim")
    def test_WHEN_analogue_value_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, test_value))
        self.ca.assert_that_pv_is_number(pv_name, test_value, 0.001, timeout=40)

    @parameterized.expand(parameterized_list(zip(ANALOGUE_IN_PV_NAMES, FLOAT_TEST_VALUES)))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_analogue_value_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self.ca.set_pv_value("SIM:{}".format(pv_name), test_value)
        self.ca.assert_that_pv_is_number(pv_name, test_value, 0.001, timeout=40)

    @parameterized.expand(parameterized_list(AUTO_MANUAL_PV_NAMES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_value_manual_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, 2))
        self.ca.assert_that_pv_is(pv_name, "AUTOMATIC", timeout=40)

        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, 1))
        self.ca.assert_that_pv_is(pv_name, "MANUAL", timeout=40)

    @parameterized.expand(parameterized_list(AUTO_MANUAL_PV_NAMES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_value_auto_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, 1))
        self.ca.assert_that_pv_is(pv_name, "MANUAL", timeout=40)

        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, 2))
        self.ca.assert_that_pv_is(pv_name, "AUTOMATIC", timeout=40)

    @parameterized.expand(parameterized_list(AUTO_MANUAL_PV_NAMES))
    @skip_if_devsim("sim pvs not available in recsim")
    def test_WHEN_value_manual_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name):
        self.ca.set_pv_value("SIM:{}".format(pv_name), 1)
        self.ca.assert_that_pv_is(pv_name, "AUTOMATIC", timeout=40)

        self.ca.set_pv_value("SIM:{}".format(pv_name), 0)
        self.ca.assert_that_pv_is(pv_name, "MANUAL", timeout=40)

    @parameterized.expand(parameterized_list(AUTO_MANUAL_PV_NAMES))
    @skip_if_devsim("sim pvs not available in recsim")
    def test_WHEN_value_auto_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name):
        self.ca.set_pv_value("SIM:{}".format(pv_name), 0)
        self.ca.assert_that_pv_is(pv_name, "MANUAL", timeout=40)

        self.ca.set_pv_value("SIM:{}".format(pv_name), 1)
        self.ca.assert_that_pv_is(pv_name, "AUTOMATIC", timeout=40)

    @parameterized.expand(parameterized_list(CONTROL_VALVE_POSITION_VALUES))
    @skip_if_recsim("lewis backdoor not available in devsim")
    def test_WHEN_CNTRL_VALVE_120_position_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = CONTROL_VALVE_POSITION_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device("set_memory", ("CNTRL_VALVE_120:POSITION", index_test_value))
        self.ca.assert_that_pv_is("CNTRL_VALVE_120:POSITION", test_value, timeout=40)

    @parameterized.expand(parameterized_list(CONTROL_VALVE_POSITION_VALUES))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_CNTRL_VALVE_120_position_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = CONTROL_VALVE_POSITION_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:CNTRL_VALVE_120:POSITION", index_test_value)
        self.ca.assert_that_pv_is("CNTRL_VALVE_120:POSITION", test_value, timeout=40)

    @parameterized.expand(parameterized_list(CONTROL_VALVE_POSITION_VALUES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_CNTRL_VALVE_121_position_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = CONTROL_VALVE_POSITION_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device("set_memory", ("CNTRL_VALVE_121:POSITION", index_test_value))
        self.ca.assert_that_pv_is("CNTRL_VALVE_121:POSITION", test_value, timeout=40)

    @parameterized.expand(parameterized_list(CONTROL_VALVE_POSITION_VALUES))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_CNTRL_VALVE_121_position_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = CONTROL_VALVE_POSITION_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:CNTRL_VALVE_121:POSITION", index_test_value)
        self.ca.assert_that_pv_is("CNTRL_VALVE_121:POSITION", test_value, timeout=40)

    @parameterized.expand(parameterized_list(PURIFIER_STATUS_VALUES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_purifier_status_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = PURIFIER_STATUS_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device("set_memory", ("PURIFIER:STATUS", index_test_value))
        self.ca.assert_that_pv_is("PURIFIER:STATUS", test_value, timeout=40)

    @parameterized.expand(parameterized_list(PURIFIER_STATUS_VALUES))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_purifier_status_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = PURIFIER_STATUS_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:PURIFIER:STATUS", index_test_value)
        self.ca.assert_that_pv_is("PURIFIER:STATUS", test_value, timeout=40)

    @parameterized.expand(parameterized_list(COMPRESSOR_STATUS_VALUES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_compressor_status_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = COMPRESSOR_STATUS_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device("set_memory", ("CMPRSSR:STATUS", index_test_value))
        self.ca.assert_that_pv_is("CMPRSSR:STATUS", test_value, timeout=40)

    @parameterized.expand(parameterized_list(COMPRESSOR_STATUS_VALUES))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_compressor_status_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = COMPRESSOR_STATUS_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:CMPRSSR:STATUS", index_test_value)
        self.ca.assert_that_pv_is("CMPRSSR:STATUS", test_value, timeout=40)

    @parameterized.expand(parameterized_list(COLDBOX_STATUS_VALUES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_coldbox_status_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = COLDBOX_STATUS_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device("set_memory", ("COLDBOX:STATUS", index_test_value))
        self.ca.assert_that_pv_is("COLDBOX:STATUS", test_value, timeout=40)

    @parameterized.expand(parameterized_list(COLDBOX_STATUS_VALUES))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_coldbox_status_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = COLDBOX_STATUS_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:COLDBOX:STATUS", index_test_value)
        self.ca.assert_that_pv_is("COLDBOX:STATUS", test_value, timeout=40)

    @parameterized.expand(parameterized_list(itertools.product(VALVE_STATUS_PVS, VALVE_STATUS_VALUES)))
    @skip_if_recsim("lewis backddor not available in recsim")
    def test_WHEN_valve_status_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        index_test_value = VALVE_STATUS_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, index_test_value))
        self.ca.assert_that_pv_is(pv_name, test_value, timeout=40)

    @parameterized.expand(parameterized_list(itertools.product(VALVE_STATUS_PVS, VALVE_STATUS_VALUES)))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_valve_status_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        index_test_value = VALVE_STATUS_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:{}".format(pv_name), index_test_value)
        self.ca.assert_that_pv_is(pv_name, test_value, timeout=40)

    # Liquefier alarms are tested separately because in the memory map they are unsigned integers. The C driver does
    # not support unsigned 16 bit integers directly, but the value is put into a longin record, which should display
    # the unsigned 16 bit integer correctly. Therefore, we have tests that check if these two records can correctly
    # read the largest possible unsigned 16 bit integer value.

    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_liquefier_alarm_1_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_run_function_on_device("set_memory", ("LIQUEFIER:ALARM1", 65535))
        self.ca.assert_that_pv_is("LIQUEFIER:ALARM1", 65535, timeout=40)

    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_liquefier_alarm_1_set_sim_pv_THEN_ioc_read_correctly(self):
        self.ca.set_pv_value("SIM:{}".format("LIQUEFIER:ALARM1"), 65535)
        self.ca.assert_that_pv_is("LIQUEFIER:ALARM1", 65535, timeout=40)

    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_liquefier_alarm_2_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_run_function_on_device("set_memory", ("LIQUEFIER:ALARM1", 65535))
        self.ca.assert_that_pv_is("LIQUEFIER:ALARM1", 65535, timeout=40)

    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_liquefier_alarm_2_set_sim_pv_THEN_ioc_read_correctly(self):
        self.ca.set_pv_value("SIM:{}".format("LIQUEFIER:ALARM1"), 65535)
        self.ca.assert_that_pv_is("LIQUEFIER:ALARM1", 65535, timeout=40)
