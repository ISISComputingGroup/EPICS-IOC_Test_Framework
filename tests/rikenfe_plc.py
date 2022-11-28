import time
import unittest

from parameterized import parameterized

from utils.testing import parameterized_list
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister

# Device prefix
DEVICE_PREFIX = "SCHNDR_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SCHNDR"),
        "macros": {
            "DEVCMD1": "RIKENFE"
        },
    },
]


TEST_MODES = [TestModes.RECSIM]


class RikenFEPLCTests(unittest.TestCase):
    """
    Tests for the RIKEN FE PLC
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0)

    @parameterized.expand(parameterized_list([
        (0, "SOLENOID:COMMS:STAT", "Comms OK"),
        (0, "SOLENOID:GH7:STAT", "GH7 Error"),
        (1, "SOLENOID:COMMS:STAT", "Comms Error"),
        (1, "SOLENOID:GH7:STAT", "GH7 Error"),
        (2, "SOLENOID:COMMS:STAT", "Comms OK"),
        (2, "SOLENOID:GH7:STAT", "GH7 OK"),
    ]))
    def test_GIVEN_value_written_to_raw_pv_THEN_appropriate_bit_value_is_as_expected(
            self, _, raw_value, pv_name, expected_value):

        self.ca.set_pv_value("SIM:SOLENOID:STAT:RAW", raw_value)
        self.ca.assert_that_pv_is(pv_name, expected_value)

    @parameterized.expand(parameterized_list([
    ("SIM:LV1:OPEN:SP:OUT", "LV1:OPEN:SP"),
    ("SIM:LV2:OPEN:SP:OUT", "LV2:OPEN:SP"),
    ("SIM:LV3:OPEN:SP:OUT", "LV3:OPEN:SP"),
    ("SIM:LV4:OPEN:SP:OUT", "LV4:OPEN:SP"),
    ("SIM:LV5:OPEN:SP:OUT", "LV5:OPEN:SP"),
    ("SIM:LV6:OPEN:SP:OUT", "LV6:OPEN:SP"),
    ("SIM:LV7:OPEN:SP:OUT", "LV7:OPEN:SP"),
    ("SIM:AMGV:OPEN:SP:OUT", "AMGV:OPEN:SP"),
    ("SIM:FSOV:OPEN:SP:OUT", "FSOV:OPEN:SP"),
    ]))
    def test_GIVEN_valve_open_requested_THEN_correct_sequence_generated(
            self, _, sim_pv_name, out_pv_name):

        # Explicitly set PV to initial value to remove alarm
        self.ca.set_pv_value(sim_pv_name, 0)

        # Check PV has given value
        self.ca.assert_that_pv_is(sim_pv_name, 0)

        # Check PV has no alarm (otherwise assertion below would fail)
        self.ca.assert_that_pv_alarm_is(sim_pv_name, self.ca.Alarms.NONE)

        with self.ca.assert_that_pv_monitor_gets_values(sim_pv_name, [0, 1, 0]):

            # Force process of record
            self.ca.process_pv(out_pv_name)

            # Allow _up to_ 5 seconds for PV to change value, and monitor to notice
            time.sleep(5)
