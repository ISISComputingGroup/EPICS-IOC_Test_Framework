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
            "PLCIP": "127.0.0.1",
            "PLCNODE": 58,
        },
        "emulator": "fins",
    },
]

TEST_MODES = [TestModes.DEVSIM]

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
            "COLDBOX:PT112:PRESSURE", "COLDBOX:CV103", "COLDBOX:CV111", "MOTHER_DEWAR:HE_LEVEL", "PURIFIER:LEVEL",
            "IMPURE_HE_SUPPLY:PRESSURE", "CMPRSSR:LOW_CNTRL_PRESSURE", "CMPRSSR:HIGH_CNTRL_PRESSURE", "CV2250",
            "CV2150", "CV2160", "LIQUID_NITROGEN:STATUS", "LIQUEFIER:ALARM1", "LIQUEFIER:ALARM2",
            "MCP:LIQUID_HE_INVENTORY"]

AUTO_MANUAL_PV_NAMES = ["CNTRL_VALVE_120:MODE", "CNTRL_VALVE_121:MODE", "LOW_PRESSURE:MODE", "HIGH_PRESSURE:MODE",
                        "TIC106:MODE", "PIC112:MODE"]

CV_POSITION_VALUES = ["Opening", "Closing", "No movement"]

PURIFIER_STATUS_VALUES = ["OFF", "FLUSHING", "COOLDOWN 1", "COOLDOWN 2", "CLEANING MODE", "REGENERATION", "STANDBY"]

COMPRESSOR_STATUS_VALUES = ["NOT READY TO START", "READY TO START", "RUNNING"]

COLDBOX_STATUS_VALUES = ["IN COOLDOWN", "RUNNING", "NOT RUNNING"]

VALVE_STATUS_PVS = ["CNTRL_VALVE_112:STATUS", "CNTRL_VALVE_2150:STATUS", "CNTRL_VALVE_2160:STATUS",
                    "CNTRL_VALVE_2250:STATUS"]

VALVE_STATUS_VALUES = ["OPENING", "SWEEPING", "CLOSED", "FAULT"]

TEST_VALUES = range(1, len(PV_NAMES) + 1)


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

    @staticmethod
    def _get_index_value(list_of_test_values, test_value):
        """
        Returns a 1-based index of the given test value in the given list.
        :param list_of_test_values: the list of test values within which we search for the given test value.
        :param test_value: the test value we want the index for.
        :return: a 1-based index of the test value.
        """
        return list_of_test_values.index(test_value) + 1

    # @parameterized.expand(parameterized_list(zip(PV_NAMES, TEST_VALUES)))
    # @skip_if_recsim("lewis backdoor not supported in recsim")
    # def test_WHEN_value_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name, test_value):
    #     self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, test_value))
    #     self.ca.assert_that_pv_is(pv_name, test_value, timeout=40)
    #
    # @parameterized.expand(parameterized_list(zip(PV_NAMES, TEST_VALUES)))
    # @skip_if_devsim("sim pvs not available in devsim")
    # def test_WHEN_value_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name, test_value):
    #     self.ca.set_pv_value("SIM:{}".format(pv_name), test_value)
    #     self.ca.assert_that_pv_is(pv_name, test_value)
    #
    @parameterized.expand(parameterized_list(AUTO_MANUAL_PV_NAMES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_value_manual_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, 1))
        self.ca.assert_that_pv_is(pv_name, "AUTO", timeout=40)

        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, 0))
        self.ca.assert_that_pv_is(pv_name, "MANUAL", timeout=40)

    @parameterized.expand(parameterized_list(AUTO_MANUAL_PV_NAMES))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_value_auto_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, 0))
        self.ca.assert_that_pv_is(pv_name, "MANUAL", timeout=40)

        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, 1))
        self.ca.assert_that_pv_is(pv_name, "AUTO", timeout=40)

    @parameterized.expand(parameterized_list(AUTO_MANUAL_PV_NAMES))
    @skip_if_devsim("sim pvs not available in recsim")
    def test_WHEN_value_manual_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name):
        self.ca.set_pv_value("SIM:{}".format(pv_name), 1)
        self.ca.assert_that_pv_is(pv_name, "AUTO")

        self.ca.set_pv_value("SIM:{}".format(pv_name), 0)
        self.ca.assert_that_pv_is(pv_name, "MANUAL")

    @parameterized.expand(parameterized_list(AUTO_MANUAL_PV_NAMES))
    @skip_if_devsim("sim pvs not available in recsim")
    def test_WHEN_value_auto_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name):
        self.ca.set_pv_value("SIM:{}".format(pv_name), 0)
        self.ca.assert_that_pv_is(pv_name, "MANUAL")

        self.ca.set_pv_value("SIM:{}".format(pv_name), 1)
        self.ca.assert_that_pv_is(pv_name, "AUTO")
    #
    # @parameterized.expand(parameterized_list(CV_POSITION_VALUES))
    # @skip_if_recsim("lewis backdoor not available in recsim")
    # def test_WHEN_CV120_position_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
    #     index_test_value = HeliumRecoveryPLCTests._get_index_value(CV_POSITION_VALUES, test_value)
    #     self._lewis.backdoor_run_function_on_device("set_memory", ("CV120:POSITION", index_test_value))
    #     self.ca.assert_that_pv_is("CV120:POSITION", test_value, timeout=40)
    #
    # @parameterized.expand(parameterized_list(CV_POSITION_VALUES))
    # @skip_if_recsim("lewis backdoor not available in recsim")
    # def test_WHEN_CV121_position_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
    #     index_test_value = HeliumRecoveryPLCTests._get_index_value(CV_POSITION_VALUES, test_value)
    #     self._lewis.backdoor_run_function_on_device("set_memory", ("CV121:POSITION", index_test_value))
    #     self.ca.assert_that_pv_is("CV121:POSITION", test_value, timeout=40)
    #
    # @parameterized.expand(parameterized_list(CV_POSITION_VALUES))
    # @skip_if_devsim("sim pvs not available in devsim")
    # def test_WHEN_CV120_position_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
    #     index_test_value = HeliumRecoveryPLCTests._get_index_value(CV_POSITION_VALUES, test_value)
    #     self.ca.set_pv_value("SIM:CV120:POSITION", index_test_value)
    #     self.ca.assert_that_pv_is("CV120:POSITION", test_value)
    #
    # @parameterized.expand(parameterized_list(CV_POSITION_VALUES))
    # @skip_if_devsim("sim pvs not available in devsim")
    # def test_WHEN_CV121_position_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
    #     index_test_value = HeliumRecoveryPLCTests._get_index_value(CV_POSITION_VALUES, test_value)
    #     self.ca.set_pv_value("SIM:CV121:POSITION", index_test_value)
    #     self.ca.assert_that_pv_is("CV121:POSITION", test_value)
    #
    # @parameterized.expand(parameterized_list(PURIFIER_STATUS_VALUES))
    # @skip_if_recsim("lewis backdoor not available in recsim")
    # def test_WHEN_purifier_status_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
    #     index_test_value = HeliumRecoveryPLCTests._get_index_value(PURIFIER_STATUS_VALUES, test_value)
    #     self._lewis.backdoor_run_function_on_device("set_memory", ("PURIFIER:STATUS", index_test_value))
    #     self.ca.assert_that_pv_is("PURIFIER:STATUS", test_value, timeout=40)
    #
    # @parameterized.expand(parameterized_list(PURIFIER_STATUS_VALUES))
    # @skip_if_devsim("sim pvs not available in devsim")
    # def test_WHEN_purifier_status_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
    #     index_test_value = HeliumRecoveryPLCTests._get_index_value(PURIFIER_STATUS_VALUES, test_value)
    #     self.ca.set_pv_value("SIM:PURIFIER:STATUS", index_test_value)
    #     self.ca.assert_that_pv_is("PURIFIER:STATUS", test_value, timeout=40)
    #
    # @parameterized.expand(parameterized_list(COMPRESSOR_STATUS_VALUES))
    # @skip_if_devsim("sim pvs not available in devsim")
    # def test_WHEN_purifier_status_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
    #     index_test_value = HeliumRecoveryPLCTests._get_index_value(COMPRESSOR_STATUS_VALUES, test_value)
    #     self.ca.set_pv_value("SIM:CMPRSSR:STATUS", index_test_value)
    #     self.ca.assert_that_pv_is("CMPRSSR:STATUS", test_value, timeout=40)
    #
    # @parameterized.expand(parameterized_list(COMPRESSOR_STATUS_VALUES))
    # @skip_if_recsim("lewis backdoor not available in recsim")
    # def test_WHEN_compressor_status_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
    #     index_test_value = HeliumRecoveryPLCTests._get_index_value(COMPRESSOR_STATUS_VALUES, test_value)
    #     self._lewis.backdoor_run_function_on_device("set_memory", ("CMPRSSR:STATUS", index_test_value))
    #     self.ca.assert_that_pv_is("CMPRSSR:STATUS", test_value, timeout=40)
    #
    # @parameterized.expand(parameterized_list(COLDBOX_STATUS_VALUES))
    # @skip_if_devsim("sim pvs not available in devsim")
    # def test_WHEN_purifier_status_set_sim_pv_THEN_ioc_read_correctly(self, _, test_value):
    #     index_test_value = HeliumRecoveryPLCTests._get_index_value(COLDBOX_STATUS_VALUES, test_value)
    #     self.ca.set_pv_value("SIM:COLDBOX:STATUS", index_test_value)
    #     self.ca.assert_that_pv_is("COLDBOX:STATUS", test_value, timeout=40)
    #
    # @parameterized.expand(parameterized_list(COLDBOX_STATUS_VALUES))
    # @skip_if_recsim("lewis backdoor not available in recsim")
    # def test_WHEN_compressor_status_set_backdoor_THEN_ioc_read_correctly(self, _, test_value):
    #     index_test_value = HeliumRecoveryPLCTests._get_index_value(COLDBOX_STATUS_VALUES, test_value)
    #     self._lewis.backdoor_run_function_on_device("set_memory", ("COLDBOX:STATUS", index_test_value))
    #     self.ca.assert_that_pv_is("COLDBOX:STATUS", test_value, timeout=40)

    @parameterized.expand(parameterized_list(itertools.product(VALVE_STATUS_PVS, VALVE_STATUS_VALUES)))
    @skip_if_devsim("sim pvs not available in devsim")
    def test_WHEN_valve_status_set_sim_pv_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        index_test_value = HeliumRecoveryPLCTests._get_index_value(VALVE_STATUS_VALUES, test_value)
        self.ca.set_pv_value("SIM:{}".format(pv_name), index_test_value)
        self.ca.assert_that_pv_is(pv_name, test_value, timeout=40)

    @parameterized.expand(parameterized_list(itertools.product(VALVE_STATUS_PVS, VALVE_STATUS_VALUES)))
    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_compressor_status_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        index_test_value = HeliumRecoveryPLCTests._get_index_value(VALVE_STATUS_VALUES, test_value)
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, index_test_value))
        self.ca.assert_that_pv_is(pv_name, test_value, timeout=40)
