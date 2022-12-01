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
    Tests for the RIKEN Front End PLC
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0)

    # TODO: add cases for each of the remaining bits i.e. 0,1,2,4,16,32,64,
    # Also PVs in RIKENFE_Vacuum_Valve_Interlock_Status template

    @parameterized.expand(parameterized_list([
        (0, "SOLENOID:COMMS:STAT", "Comms OK"),
        (0, "SOLENOID:GH7:STAT", "GH7 Error"),
        (1, "SOLENOID:COMMS:STAT", "Comms Error"),
        (1, "SOLENOID:GH7:STAT", "GH7 Error"),
        (2, "SOLENOID:COMMS:STAT", "Comms OK"),
        (2, "SOLENOID:GH7:STAT", "GH7 OK"),
        (4, "SOLENOID:GH8:STAT", "GH8 OK"),
        (8, "SOLENOID:CRYO_SYS:STAT", "Cryo System OK"),
        (16, "SOLENOID:COOLDOWN:STAT", "Cooldown Complete"),
        (32, "SOLENOID:MAG_EXCIT:STAT", "Magnet Excitation ON"),
        (64, "SOLENOID:COMPRESSOR:STAT", "Compressor ON"),
        (0, "LV1:ILK:STAT:COMMS:STAT", "Comms Error"),
        (1, "LV1:ILK:STAT:COMMS:STAT", "Comms OK"),
        (1, "LV2:ILK:STAT:FSOV:STAT", "FSOV Opened"),
        (2, "LV3:ILK:STAT:GH28:STAT", "GH28 OK"),
        (4, "LV4:ILK:STAT:BIT3CONSTANT:STAT", "0"),
        (8, "LV5:ILK:STAT:GH36:STAT", "GH36 OK"),
        (16, "LV6:ILK:STAT:BIT5CONSTANT:STAT", "0"),
        (32, "LV7:ILK:STAT:BB4CLOSE:STAT", "!BB4 Close Command"),
        (64, "AMGV:ILK:STAT:BIT7CONSTANT:STAT", "1"),
        (128, "FSOV:ILK:STAT:EPB_FSOV:STAT", "!EPB_FSOV"),
        (128, "BPV1:ILK:STAT:BPV1CLOSE:STAT", "!Close BPV1"),
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
