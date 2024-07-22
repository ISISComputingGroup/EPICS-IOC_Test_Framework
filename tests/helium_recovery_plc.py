import itertools
import os
import unittest
import random

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import (
    get_running_lewis_and_ioc,
    parameterized_list,
    skip_if_recsim,
    skip_if_devsim,
)

# Device prefix
DEVICE_PREFIX = "FINS_01"

IOC_NAME = "FINS"
TEST_PATH = os.path.join(EPICS_TOP, "ioc", "master", IOC_NAME, "exampleSettings", "HELIUM_RECOVERY")

IOC_PREFIX = "HA:HLM"

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

# names of PVs for memory locations that store 16 bit integers, and that do not need a calc record to divide the value
# by 10
INT16_NO_CALC_PV_NAMES = ["HEARTBEAT", "COLDBOX:TURBINE_100:SPEED", "COLDBOX:TURBINE_101:SPEED"]

INT16_NO_CALC_TEST_VALUES = range(1, len(INT16_NO_CALC_PV_NAMES) + 1)

INT16_PV_NAMES = [
    "MCP:BANK1:TS2",
    "MCP:BANK1:TS1",
    "MCP1:BANK2:IMPURE_HE",
    "MCP2:BANK2:IMPURE_HE",
    "MCP1:BANK3:MAIN_HE_STORAGE",
    "MCP2:BANK3:MAIN_HE_STORAGE",
    "MCP1:BANK4:DLS_HE_STORAGE",
    "MCP2:BANK4:DLS_HE_STORAGE",
    "MCP1:BANK5:SPARE_STORAGE",
    "MCP2:BANK5:SPARE_STORAGE",
    "MCP1:BANK6:SPARE_STORAGE",
    "MCP2:BANK6:SPARE_STORAGE",
    "MCP1:BANK7:SPARE_STORAGE",
    "MCP2:BANK7:SPARE_STORAGE",
    "MCP1:BANK8:SPARE_STORAGE",
    "MCP2:BANK8:SPARE_STORAGE",
    "MCP:INLET:PRESSURE",
    "MCP:EXTERNAL_TEMP",
    "GAS_LIQUEFACTION:MASS_FLOW",
    "HE_FILLS:MASS_FLOW",
    "CMPRSSR:INTERNAL_TEMP",
    "COLDBOX:HE_TEMP",
    "COLDBOX:HE_TEMP:LIMIT",
    "TRANSPORT_DEWAR:PRESSURE",
    "HE_PURITY",
    "DEW_POINT",
    "FLOW_METER:TS2:EAST",
    "TS2:EAST:O2",
    "FLOW_METER:TS2:WEST",
    "TS2:WEST:O2",
    "TS1:NORTH:O2",
    "TS1:SOUTH:O2",
    "FLOW_METER:TS1:WINDOW",
    "FLOW_METER:TS1:SHUTTER",
    "FLOW_METER:TS1:VOID",
    "BANK1:TS2:RSPPL:AVG_PURITY",
    "BANK1:TS1:RSPPL:AVG_PURITY",
    "BANK2:IMPURE_HE:AVG_PURITY",
    "BANK3:MAIN_STRG:AVG_PURITY",
    "BANK4:DLS_STRG:AVG_PURITY",
    "BANK5:SPR_STRG:AVG_PURITY",
    "BANK6:SPR_STRG:AVG_PURITY",
    "BANK7:SPR_STRG:AVG_PURITY",
    "BANK8:SPR_STRG:AVG_PURITY",
    "COLDBOX:T106:TEMP",
    "COLDBOX:TT111:TEMP",
    "COLDBOX:PT102:PRESSURE",
    "BUFFER:PT203:PRESSURE",
    "PURIFIER:TT104:TEMP",
    "PURIFIER:TT102:TEMP",
    "COLDBOX:TT108:TEMP",
    "COLDBOX:PT112:PRESSURE",
    "COLDBOX:CNTRL_VALVE_103",
    "COLDBOX:CNTRL_VALVE_111",
    "COLDBOX:CNTRL_VALVE_112",
    "MOTHER_DEWAR:HE_LEVEL",
    "PURIFIER:LEVEL",
    "IMPURE_HE_SUPPLY:PRESSURE",
    "CMPRSSR:LOW_CNTRL_PRESSURE",
    "CMPRSSR:HIGH_CNTRL_PRESSURE",
    "CNTRL_VALVE_2250",
    "CNTRL_VALVE_2150",
    "CNTRL_VALVE_2160",
    "MCP:LIQUID_HE_INVENTORY",
]

INT16_TEST_VALUES = range(1, len(INT16_PV_NAMES) + 1)

# names of PVs for memory locations that store 32 bit integers
DWORD_PV_NAMES = [
    "GC:R108:U40",
    "GC:R108:DEWAR_FARM",
    "GC:R55:TOTAL",
    "GC:R55:NORTH",
    "GC:R55:SOUTH",
    "GC:MICE_HALL",
    "GC:MUON",
    "GC:PEARL_HRPD_MARI_ENGINX",
    "GC:SXD_AND_MERLIN",
    "GC:CRYO_LAB",
    "GC:MAPS_AND_VESUVIO",
    "GC:SANDALS",
    "GC:CRISP_AND_LOQ",
    "GC:IRIS_AND_OSIRIS",
    "GC:INES_AND_TOSCA",
    "GC:RIKEN",
    "GC:R80:TOTAL",
    "GC:R53",
    "GC:R80:EAST",
    "GC:WISH",
    "GC:WISH:DEWAR_FARM",
    "GC:LARMOR_AND_OFFSPEC",
    "GC:ZOOM_SANS2D_AND_POLREF",
    "GC:MAGNET_LAB",
    "GC:IMAT",
    "GC:LET_AND_NIMROD",
    "GC:R80:WEST",
]

DWORD_TEST_VALUES = range(65535, len(DWORD_PV_NAMES) + 65535)

# list of names for the ai records. It is a separate list as we want to test floating point values with these PVs
ANALOGUE_IN_PV_NAMES = [
    "MASS_FLOW:HE_RSPPL:TS2:EAST",
    "MASS_FLOW:HE_RSPPL:TS2:WEST",
    "MASS_FLOW:HE_RSPPL:TS1:VOID",
    "MASS_FLOW:HE_RSPPL:TS1:WNDW",
    "MASS_FLOW:HE_RSPPL:TS1:SHTR",
]

ANALOGUE_TEST_VALUES = [2.648, 3.028, 5.921, 10.596, 13.207]

AUTO_MANUAL_PV_NAMES = [
    "CNTRL_VALVE_120:MODE",
    "CNTRL_VALVE_121:MODE",
    "LOW_PRESSURE:MODE",
    "HIGH_PRESSURE:MODE",
    "TIC106:MODE",
    "PIC112:MODE",
]

CONTROL_VALVE_POSITION_VALUES = ["Opening", "Closing", "No movement"]

PURIFIER_STATUS_VALUES = [
    "OFF",
    "FLUSHING",
    "COOLDOWN 1",
    "COOLDOWN 2",
    "CLEANING MODE",
    "REGENERATION",
    "STANDBY",
]

COMPRESSOR_STATUS_VALUES = ["NOT READY TO START", "READY TO START", "RUNNING"]

COLDBOX_STATUS_VALUES = ["IN COOLDOWN", "RUNNING", "NOT RUNNING"]

VALVE_STATUS_PVS = [
    "MOTORISED_VALVE_108:STATUS",
    "CNTRL_VALVE_112:STATUS",
    "CNTRL_VALVE_2150:STATUS",
    "CNTRL_VALVE_2160:STATUS",
    "CNTRL_VALVE_2250:STATUS",
    "MOTORISED_VALVE_110:STATUS",
    "MOTORISED_VALVE_160:STATUS",
    "MOTORISED_VALVE_163:STATUS",
    "MOTORISED_VALVE_167:STATUS",
    "MOTORISED_VALVE_172:STATUS",
    "MOTORISED_VALVE_174:STATUS",
    "MOTORISED_VALVE_175:STATUS",
    "MOTORISED_VALVE_176:STATUS",
    "MOTORISED_VALVE_177:STATUS",
    "MOTORISED_VALVE_178:STATUS",
    "CNTRL_VALVE_103:STATUS",
    "CNTRL_VALVE_111:STATUS",
]

VALVE_STATUS_VALUES = ["Opened", "Sweeping", "Closed", "Fault"]

LIQUEFIER_ALARMS = [
    "POWER_FAILURE",
    "TURBINE1:BRAKE_TEMP",
    "TURBINE2:BRAKE_TEMP",
    "TURBINE1:OVERSPEED",
    "TURBINE1:TRIPPED_CMPRSSR",
    "TURBINE2:OVERSPEED",
    "TURBINE2:TRIPPED_CMPRSSR",
    "BACKING_PRESSURE",
    "ORS_COALESCER:LEVEL",
    "ORS:TEMPERATURE",
    "TS105:UNDERCOOL",
    "TTX108:UNDERCOOL",
    "TURBINE:UNDERCOOL",
    "TURBINE:MALFUNCTION",
    "PURIFIER:UNDERCOOL",
    "LIS107",
    "PLANT_AUTOSTOP:TIMEOUT",
    "EMERGENCY_STOP",
    "230VAC:FUSE",
    "24VDC:FUSE",
    "LTX107:FUSE",
    "SAFTY_CHAIN_TURBINE",
    "PSL2951",
    "FI3100:COOLING",
]


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

    # The heartbeat and coldbox turbine speeds are tested separately despite storing 16 bit integers because it does
    # not have a calc record that divides the value by 10. The heartbeat is not tested with negative numbers because it
    # does not support them and does not need to. Because of that, it has no associated _RAW PV, and has a 0.5 second
    # scan rate regardless of the global scan rate, so it does not need to be manually processed by the test.
    @parameterized.expand(
        parameterized_list(zip(INT16_NO_CALC_PV_NAMES, INT16_NO_CALC_TEST_VALUES))
    )
    @skip_if_recsim("lewis backdoor not supported in recsim")
    def test_WHEN_int16_no_calc_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, test_value))

        if pv_name != "HEARTBEAT":
            self.ca.process_pv("{}:_RAW".format(pv_name))

        self.ca.assert_that_pv_after_processing_is(pv_name, test_value)

    @parameterized.expand(
        parameterized_list(zip(INT16_NO_CALC_PV_NAMES, INT16_NO_CALC_TEST_VALUES))
    )
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_int16_no_calc_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self.ca.set_pv_value("SIM:{}".format(pv_name), test_value)

        if pv_name != "HEARTBEAT":
            self.ca.process_pv("{}:_RAW".format(pv_name))

        self.ca.assert_that_pv_after_processing_is(pv_name, test_value)

    @parameterized.expand(
        parameterized_list(zip(INT16_NO_CALC_PV_NAMES, INT16_NO_CALC_TEST_VALUES))
    )
    @skip_if_recsim("lewis backdoor not supported in recsim")
    def test_WHEN_int16_no_calc_set_negative_value_backdoor_THEN_ioc_read_correctly(
        self, _, pv_name, test_value
    ):
        if pv_name == "HEARTBEAT":
            self.skipTest("HEARTBEAT does not have support for negative values")

        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, -test_value))
        self.ca.process_pv("{}:_RAW".format(pv_name))
        self.ca.assert_that_pv_after_processing_is(pv_name, -test_value)

    @parameterized.expand(
        parameterized_list(zip(INT16_NO_CALC_PV_NAMES, INT16_NO_CALC_TEST_VALUES))
    )
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_int16_no_calc_set_negative_value_sim_pv_THEN_ioc_read_correctly(
        self, _, pv_name, test_value
    ):
        if pv_name == "HEARTBEAT":
            self.skipTest("HEARTBEAT does not have support for negative values")

        self.ca.set_pv_value("SIM:{}".format(pv_name), -test_value)
        self.ca.process_pv("{}:_RAW".format(pv_name))
        self.ca.assert_that_pv_after_processing_is(pv_name, -test_value)

    @parameterized.expand(parameterized_list(zip(INT16_PV_NAMES, INT16_TEST_VALUES)))
    @skip_if_recsim("lewis backdoor not supported in recsim")
    def test_WHEN_int16_value_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, test_value))
        self.ca.process_pv("{}:_RAW".format(pv_name))
        self.ca.assert_that_pv_is(pv_name, test_value / 10)

    @parameterized.expand(parameterized_list(zip(INT16_PV_NAMES, INT16_TEST_VALUES)))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_int16_value_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self.ca.set_pv_value("SIM:{}".format(pv_name), test_value)
        self.ca.process_pv("{}:_RAW".format(pv_name))
        self.ca.assert_that_pv_is(pv_name, test_value / 10)

    @parameterized.expand(parameterized_list(zip(INT16_PV_NAMES, INT16_TEST_VALUES)))
    @skip_if_recsim("lewis backdoor not supported in recsim")
    def test_WHEN_int16_value_set_negative_value_backdoor_THEN_ioc_read_correctly(
        self, _, pv_name, test_value
    ):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, -test_value))
        self.ca.process_pv("{}:_RAW".format(pv_name))
        self.ca.assert_that_pv_is(pv_name, -test_value / 10)

    @parameterized.expand(parameterized_list(zip(INT16_PV_NAMES, INT16_TEST_VALUES)))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_int16_value_set_negative_value_sim_pv_THEN_ioc_read_correctly(
        self, _, pv_name, test_value
    ):
        self.ca.set_pv_value("SIM:{}".format(pv_name), -test_value)
        self.ca.process_pv("{}:_RAW".format(pv_name))
        self.ca.assert_that_pv_is(pv_name, -test_value / 10)

    @parameterized.expand(parameterized_list(zip(DWORD_PV_NAMES, DWORD_TEST_VALUES)))
    @skip_if_recsim("lewis backdoor not supported in recsim")
    def test_WHEN_int32_value_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, test_value))
        self.ca.assert_that_pv_after_processing_is(pv_name, test_value)

    @parameterized.expand(parameterized_list(zip(DWORD_PV_NAMES, DWORD_TEST_VALUES)))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_int32_value_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self.ca.set_pv_value("SIM:{}".format(pv_name), test_value)
        self.ca.assert_that_pv_after_processing_is(pv_name, test_value)

    @parameterized.expand(parameterized_list(zip(ANALOGUE_IN_PV_NAMES, ANALOGUE_TEST_VALUES)))
    @skip_if_recsim("lewis backdoor not supported in recsim")
    def test_WHEN_analogue_value_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, test_value))
        self.ca.assert_that_pv_after_processing_is_number(pv_name, test_value, 0.001)

    @parameterized.expand(parameterized_list(zip(ANALOGUE_IN_PV_NAMES, ANALOGUE_TEST_VALUES)))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_analogue_value_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self.ca.set_pv_value("SIM:{}".format(pv_name), test_value)
        self.ca.assert_that_pv_after_processing_is_number(pv_name, test_value, 0.001)

    @parameterized.expand(parameterized_list(AUTO_MANUAL_PV_NAMES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_auto_manual_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name):
        self.ca.assert_that_pv_after_processing_is(pv_name, "MANUAL")

        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, 2))
        self.ca.assert_that_pv_after_processing_is(pv_name, "AUTOMATIC")

        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, 1))
        self.ca.assert_that_pv_after_processing_is(pv_name, "MANUAL")

    @parameterized.expand(parameterized_list(AUTO_MANUAL_PV_NAMES))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_auto_manual_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name):
        self.ca.assert_that_pv_after_processing_is(pv_name, "MANUAL")

        self.ca.set_pv_value("SIM:{}".format(pv_name), 1)
        self.ca.assert_that_pv_after_processing_is(pv_name, "AUTOMATIC")

        self.ca.set_pv_value("SIM:{}".format(pv_name), 0)
        self.ca.assert_that_pv_after_processing_is(pv_name, "MANUAL")

    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_liquid_nitrogen_status_set_backdoor_THEN_ioc_read_correctly(self):
        self.ca.assert_that_pv_after_processing_is("LIQUID_NITROGEN:STATUS", "Not selected")

        self._lewis.backdoor_run_function_on_device("set_memory", ("LIQUID_NITROGEN:STATUS", 2))
        self.ca.assert_that_pv_after_processing_is("LIQUID_NITROGEN:STATUS", "Selected")

        self._lewis.backdoor_run_function_on_device("set_memory", ("LIQUID_NITROGEN:STATUS", 1))
        self.ca.assert_that_pv_after_processing_is("LIQUID_NITROGEN:STATUS", "Not selected")

    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_liquid_nitrogen_status_set_sim_pv_THEN_ioc_read_correctly(self):
        self.ca.assert_that_pv_after_processing_is("LIQUID_NITROGEN:STATUS", "Not selected")

        self.ca.set_pv_value("SIM:LIQUID_NITROGEN:STATUS", 1)
        self.ca.assert_that_pv_after_processing_is("LIQUID_NITROGEN:STATUS", "Selected")

        self.ca.set_pv_value("SIM:LIQUID_NITROGEN:STATUS", 0)
        self.ca.assert_that_pv_after_processing_is("LIQUID_NITROGEN:STATUS", "Not selected")

    @parameterized.expand(parameterized_list(CONTROL_VALVE_POSITION_VALUES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_CNTRL_VALVE_120_position_set_backdoor_THEN_ioc_read_correctly(
        self, _, test_value
    ):
        index_test_value = CONTROL_VALVE_POSITION_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device(
            "set_memory", ("CNTRL_VALVE_120:POSITION", index_test_value)
        )
        self.ca.assert_that_pv_after_processing_is("CNTRL_VALVE_120:POSITION", test_value)

    @parameterized.expand(parameterized_list(CONTROL_VALVE_POSITION_VALUES))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_CNTRL_VALVE_120_position_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = CONTROL_VALVE_POSITION_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:CNTRL_VALVE_120:POSITION", index_test_value)
        self.ca.assert_that_pv_after_processing_is("CNTRL_VALVE_120:POSITION", test_value)

    @parameterized.expand(parameterized_list(CONTROL_VALVE_POSITION_VALUES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_CNTRL_VALVE_121_position_set_backdoor_THEN_ioc_read_correctly(
        self, _, test_value
    ):
        index_test_value = CONTROL_VALVE_POSITION_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device(
            "set_memory", ("CNTRL_VALVE_121:POSITION", index_test_value)
        )
        self.ca.assert_that_pv_after_processing_is("CNTRL_VALVE_121:POSITION", test_value)

    @parameterized.expand(parameterized_list(CONTROL_VALVE_POSITION_VALUES))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_CNTRL_VALVE_121_position_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = CONTROL_VALVE_POSITION_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:CNTRL_VALVE_121:POSITION", index_test_value)
        self.ca.assert_that_pv_after_processing_is("CNTRL_VALVE_121:POSITION", test_value)

    @parameterized.expand(parameterized_list(PURIFIER_STATUS_VALUES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_purifier_status_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = PURIFIER_STATUS_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device(
            "set_memory", ("PURIFIER:STATUS", index_test_value)
        )
        self.ca.assert_that_pv_after_processing_is("PURIFIER:STATUS", test_value)

    @parameterized.expand(parameterized_list(PURIFIER_STATUS_VALUES))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_purifier_status_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = PURIFIER_STATUS_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:PURIFIER:STATUS", index_test_value)
        self.ca.assert_that_pv_after_processing_is("PURIFIER:STATUS", test_value)

    @parameterized.expand(parameterized_list(COMPRESSOR_STATUS_VALUES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_compressor_status_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = COMPRESSOR_STATUS_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device(
            "set_memory", ("CMPRSSR:STATUS", index_test_value)
        )
        self.ca.assert_that_pv_after_processing_is("CMPRSSR:STATUS", test_value)

    @parameterized.expand(parameterized_list(COMPRESSOR_STATUS_VALUES))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_compressor_status_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = COMPRESSOR_STATUS_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:CMPRSSR:STATUS", index_test_value)
        self.ca.assert_that_pv_after_processing_is("CMPRSSR:STATUS", test_value)

    @parameterized.expand(parameterized_list(COLDBOX_STATUS_VALUES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_coldbox_status_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = COLDBOX_STATUS_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device(
            "set_memory", ("COLDBOX:STATUS", index_test_value)
        )
        self.ca.assert_that_pv_after_processing_is("COLDBOX:STATUS", test_value)

    @parameterized.expand(parameterized_list(COLDBOX_STATUS_VALUES))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_coldbox_status_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
        index_test_value = COLDBOX_STATUS_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:COLDBOX:STATUS", index_test_value)
        self.ca.assert_that_pv_after_processing_is("COLDBOX:STATUS", test_value)

    @parameterized.expand(
        parameterized_list(itertools.product(VALVE_STATUS_PVS, VALVE_STATUS_VALUES))
    )
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_valve_status_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        index_test_value = VALVE_STATUS_VALUES.index(test_value) + 1
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, index_test_value))
        self.ca.assert_that_pv_after_processing_is(pv_name, test_value)

    @parameterized.expand(
        parameterized_list(itertools.product(VALVE_STATUS_PVS, VALVE_STATUS_VALUES))
    )
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_valve_status_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        index_test_value = VALVE_STATUS_VALUES.index(test_value)
        self.ca.set_pv_value("SIM:{}".format(pv_name), index_test_value)
        self.ca.assert_that_pv_after_processing_is(pv_name, test_value)

    # Liquefier alarms are tested separately because in the memory map they are unsigned integers. The C driver does
    # not support unsigned 16 bit integers directly, but the value is put into a longin record, which should display
    # the unsigned 16 bit integer correctly. There are two mbbiDirect records that read from the two memory locations
    # that store alarms in the form of 16 bit integers. These tests then check that the bi records that read from the
    # mbbiDirect recors work properly.

    @parameterized.expand(parameterized_list(LIQUEFIER_ALARMS))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_liquefier_alarm_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name):
        alarm_index = LIQUEFIER_ALARMS.index(pv_name)
        mbbi_direct_pv = HeliumRecoveryPLCTests._get_liquefier_hardware_pv(alarm_index)
        test_value = HeliumRecoveryPLCTests._get_alarm_test_value(mbbi_direct_pv, alarm_index)

        raw_pv = "{}:_RAW".format(mbbi_direct_pv)
        full_pv_name = "{}:ALARM".format(pv_name)

        self.ca.process_pv(raw_pv)
        self.ca.assert_that_pv_is(full_pv_name, "OK")

        self._lewis.backdoor_run_function_on_device("set_memory", (mbbi_direct_pv, test_value))
        self.ca.process_pv(raw_pv)
        self.ca.assert_that_pv_is(full_pv_name, "IN ALARM")

        self._lewis.backdoor_run_function_on_device("set_memory", (mbbi_direct_pv, 0))
        self.ca.process_pv(raw_pv)
        self.ca.assert_that_pv_is(full_pv_name, "OK")

    @parameterized.expand(parameterized_list(LIQUEFIER_ALARMS))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_liquefier_alarm_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name):
        alarm_index = LIQUEFIER_ALARMS.index(pv_name)
        mbbi_direct_pv = HeliumRecoveryPLCTests._get_liquefier_hardware_pv(alarm_index)
        test_value = HeliumRecoveryPLCTests._get_alarm_test_value(mbbi_direct_pv, alarm_index)

        raw_pv = "{}:_RAW".format(mbbi_direct_pv)
        full_pv_name = "{}:ALARM".format(pv_name)

        self.ca.process_pv(raw_pv)
        self.ca.assert_that_pv_is(full_pv_name, "OK")

        self.ca.set_pv_value("SIM:{}".format(mbbi_direct_pv), test_value)
        self.ca.process_pv(raw_pv)
        self.ca.assert_that_pv_is(full_pv_name, "IN ALARM")

        self.ca.set_pv_value("SIM:{}".format(mbbi_direct_pv), 0)
        self.ca.process_pv(raw_pv)
        self.ca.assert_that_pv_is(full_pv_name, "OK")

    @staticmethod
    def _get_liquefier_hardware_pv(alarm_index):
        """
        The 24 alarm bi records get their value from one of two mbbi records. The first 15 get their value from the
        first, and the rest from the second one.

        Args:
            alarm_index (int): Index of the pv name in the list of alarm PVs.

        Returns (string): The name of the mbbiDirect record from where the alarm bi record gets its value.
        """
        if alarm_index < 15:
            mbbi_direct_pv = "LIQUEFIER:_ALARM1"
        else:
            mbbi_direct_pv = "LIQUEFIER:_ALARM2"

        return mbbi_direct_pv

    @staticmethod
    def _get_alarm_test_value(mbbi_direct_pv, alarm_index):
        """
        The alarm bi records get their valuer from 16 bit number in mbbiDirect records, and we need to compute the
        correct value for the mbbiDirect such that the right alarm bi record is 1 and not 0.

        Args:
            mbbi_direct_pv (string): The name of the mbbiDirect record from where the alarm bi records gets their value.
            alarm_index (int): Index of the pv name in the list of alarm PVs

        Returns:
            int: The corect test value for the mbbi record, such that the bi record being tested will have a value of
                1, or be in alarm.
        """
        if mbbi_direct_pv == "LIQUEFIER:_ALARM1":
            # We add 1 to the index because the first bit int LIQUEFIER:_ALARM1 is not used
            return 2 ** (alarm_index + 1)
        elif mbbi_direct_pv == "LIQUEFIER:_ALARM2":
            # We subtract 15 because the bi record for ALARM2 are after the 15 bi records for ALARM1 in the liquefier
            # alarms list.
            return 2 ** (alarm_index - 15)
