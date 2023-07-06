import unittest

from parameterized import parameterized

from genie_python.genie_cachannel_wrapper import InvalidEnumStringException

from common_tests.tpgx00 import Tpgx00Base
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import skip_if_recsim, parameterized_list
from enum import Enum


DEVICE_PREFIX = "TPG300_01"

IOCS = [
    {
    "name": DEVICE_PREFIX,
    "directory": get_default_ioc_dir("TPG300"),
    "macros": {
        "MODEL": "300"
    },
    "emulator": "tpgx00",
    "lewis_protocol": "tpg300",
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]

SWITCHING_FUNCTIONS = ("SEL", "1", "2", "3", "4", "A", "B")


class SFAssignment(Enum):
    OFF         = (0, "No assignment")
    A1          = (1, "A1")
    A2          = (2, "A2")
    B1          = (3, "B1")
    B2          = (4, "B1")
    A1_SELF_MON = (5, "A1 self-monitor")
    A2_SELF_MON = (6, "A2 self-monitor")
    B1_SELF_MON = (7, "B1 self-monitor")
    B2_SELF_MON = (8, "B1 self-monitor")

    def __new__(cls, value, desc):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.desc = desc
        return obj


class Units(Enum):
    mbar = 1
    Torr = 2
    Pa = 3


class InvalidUnits(Enum):
    hPascal = 0
    Micron = 4
    Volt = 5
    Ampere = 6


class ErrorStatus(Enum):
    NO_ERROR      = "No error"
    DEVICE_ERROR  = "Device error"
    NO_HARDWARE   = "No hardware"
    INVALID_PARAM = "Invalid parameter"
    SYNTAX_ERROR  = "Syntax error"


class SFStatus(Enum):
    OFF = 0
    ON  = 1


class Tpg300Tests(Tpgx00Base, unittest.TestCase):
    """
    Tests for the TPG300.
    """

    def get_prefix(self):
        return DEVICE_PREFIX
        
    def get_units(self):
        return Units

    def get_sf_assignment(self):
        return SFAssignment
    
    def get_switching_fns(self):
        return SWITCHING_FUNCTIONS
    
    
    @parameterized.expand(parameterized_list([unit.value for unit in InvalidUnits]))
    @skip_if_recsim("Requires emulator")
    def test_WHEN_invalid_unit_set_THEN_pv_goes_into_alarm(self, _, unit_name):
        self.ca.set_pv_value("UNITS:SP", unit_name)
        self.ca.assert_that_pv_is_not("UNITS", unit_name)
        self._lewis.assert_that_emulator_value_is_not("backdoor_get_unit", str(unit_name))
        self.ca.assert_that_pv_alarm_is("UNITS:SP", "INVALID")   

    # These tests would usually live in tpgx00 to be tested on both devices but this functionality only 
    # works on the 300 for now 
    def _check_switching_function_statuses(self, expected_statuses):
        self.ca.assert_that_pv_is("FUNCTION:STATUS:1:RB", str(SFStatus[expected_statuses[0]].value))
        self.ca.assert_that_pv_is("FUNCTION:STATUS:2:RB", str(SFStatus[expected_statuses[1]].value))
        self.ca.assert_that_pv_is("FUNCTION:STATUS:3:RB", str(SFStatus[expected_statuses[2]].value))
        self.ca.assert_that_pv_is("FUNCTION:STATUS:4:RB", str(SFStatus[expected_statuses[3]].value))

    @skip_if_recsim("Requires emulator")
    def test_GIVEN_function_status_set_THEN_readback_correct(self):
        function_statuses = ["OFF", "OFF", "ON", "ON", "OFF", "ON"]
        self._lewis.backdoor_run_function_on_device("backdoor_set_switching_function_status", [function_statuses])
        self._check_switching_function_statuses(function_statuses)

    @skip_if_recsim("Requires emulator")
    def test_WHEN_error_set_by_device_THEN_readback_correct(self):
        for error in ErrorStatus:
            self._lewis.backdoor_run_function_on_device("backdoor_set_error_status", [error.name])
            self.ca.assert_that_pv_is("ERROR", error.value)
    
    @skip_if_recsim("Requires emulator")
    def test_WHEN_device_disconnected_THEN_function_statuses_go_into_alarm(self):
        self._check_alarm_status_function_statuses(self.ca.Alarms.NONE)
        with self._disconnect_device():
            self._check_alarm_status_function_statuses(self.ca.Alarms.INVALID)
        
        self._check_alarm_status_function_statuses(self.ca.Alarms.NONE)
