import time
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list

# Device prefix
DEVICE_PREFIX = "SCHNDR_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SCHNDR"),
        "macros": {"DEVCMD1": "RIKENFE"},
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

    @parameterized.expand(
        parameterized_list(
            [
                (0, "SIM:SOLENOID:STAT:RAW", "SOLENOID:COMMS:STAT", "Comms OK"),
                (0, "SIM:SOLENOID:STAT:RAW", "SOLENOID:GH7:STAT", "GH7 Error"),
                (1, "SIM:SOLENOID:STAT:RAW", "SOLENOID:COMMS:STAT", "Comms Error"),
                (1, "SIM:SOLENOID:STAT:RAW", "SOLENOID:GH7:STAT", "GH7 Error"),
                (2, "SIM:SOLENOID:STAT:RAW", "SOLENOID:COMMS:STAT", "Comms OK"),
                (2, "SIM:SOLENOID:STAT:RAW", "SOLENOID:GH7:STAT", "GH7 OK"),
                (4, "SIM:SOLENOID:STAT:RAW", "SOLENOID:GH8:STAT", "GH8 OK"),
                (8, "SIM:SOLENOID:STAT:RAW", "SOLENOID:CRYO_SYS:STAT", "Cryo System OK"),
                (16, "SIM:SOLENOID:STAT:RAW", "SOLENOID:COOLDOWN:STAT", "Cooldown Complete"),
                (32, "SIM:SOLENOID:STAT:RAW", "SOLENOID:MAG_EXCIT:STAT", "Magnet Excitation ON"),
                (64, "SIM:SOLENOID:STAT:RAW", "SOLENOID:COMPRESSOR:STAT", "Compressor ON"),
                (0, "SIM:LV1:ILK:STAT:RAW", "LV1:ILK:STAT:COMMS:STAT", "-"),
                (1, "SIM:LV1:ILK:STAT:RAW", "LV1:ILK:STAT:COMMS:STAT", "Comms OK"),
                (2, "SIM:LV2:ILK:STAT:RAW", "LV2:ILK:STAT:FSOV:STAT", "FSOV Opened"),
                (4, "SIM:LV3:ILK:STAT:RAW", "LV3:ILK:STAT:GH28:STAT", "GH28 OK"),
                (8, "SIM:LV4:ILK:STAT:RAW", "LV4:ILK:STAT:BIT3CONSTANT:STAT", "0"),
                (16, "SIM:LV5:ILK:STAT:RAW", "LV5:ILK:STAT:GH36:STAT", "GH36 OK"),
                (32, "SIM:LV6:ILK:STAT:RAW", "LV6:ILK:STAT:BIT5CONSTANT:STAT", "0"),
                (64, "SIM:LV7:ILK:STAT:RAW", "LV7:ILK:STAT:BB4CLOSE:STAT", "!BB4 Close Command"),
                (128, "SIM:AMGV:ILK:STAT:RAW", "AMGV:ILK:STAT:BIT7CONSTANT:STAT", "1"),
                (256, "SIM:FSOV:ILK:STAT:RAW", "FSOV:ILK:STAT:EPB_FSOV:STAT", "!EPB_FSOV"),
                (256, "SIM:BPV1:ILK:STAT:RAW", "BPV1:ILK:STAT:BPV1CLOSE:STAT", "!Close BPV1"),
            ]
        )
    )
    def test_GIVEN_value_written_to_raw_pv_THEN_appropriate_bit_value_is_as_expected(
        self, _, raw_value, set_pv_name, get_pv_name, expected_value
    ):
        # Test to check that the MBBIDIRECT records are 'split' correctly

        self.ca.set_pv_value(set_pv_name, raw_value)
        self.ca.assert_that_pv_is(get_pv_name, expected_value)

    @parameterized.expand(
        parameterized_list(
            [
                ("SIM:LV1:OPEN:SP:OUT", "LV1:OPEN:SP"),
                ("SIM:LV2:OPEN:SP:OUT", "LV2:OPEN:SP"),
                ("SIM:LV3:OPEN:SP:OUT", "LV3:OPEN:SP"),
                ("SIM:LV4:OPEN:SP:OUT", "LV4:OPEN:SP"),
                ("SIM:LV5:OPEN:SP:OUT", "LV5:OPEN:SP"),
                ("SIM:LV6:OPEN:SP:OUT", "LV6:OPEN:SP"),
                ("SIM:LV7:OPEN:SP:OUT", "LV7:OPEN:SP"),
                ("SIM:AMGV:OPEN:SP:OUT", "AMGV:OPEN:SP"),
                ("SIM:FSOV:OPEN:SP:OUT", "FSOV:OPEN:SP"),
            ]
        )
    )
    def test_GIVEN_valve_open_requested_THEN_correct_sequence_generated(
        self, _, sim_pv_name, out_pv_name
    ):
        # PLC requires a rising edge of a register to trigger a valve to open,
        # so the IOC generates a sequence and this test checks the logic.

        # Explicitly set PV to initial value to remove alarm
        self.ca.set_pv_value(sim_pv_name, 0)

        # Check PV has given value
        self.ca.assert_that_pv_is(sim_pv_name, 0)

        # Check PV has no alarm (otherwise assertion below would fail)
        self.ca.assert_that_pv_alarm_is(sim_pv_name, self.ca.Alarms.NONE)

        with self.ca.assert_that_pv_monitor_gets_values(sim_pv_name, [0, 1, 0]):
            # Force process of record
            self.ca.process_pv(out_pv_name)

            # Allow _up to_ 5 seconds for the PV to change value and the monitor to notice
            time.sleep(5)

    @parameterized.expand(
        parameterized_list(
            [
                ("SIM:RQ1:TEMPMON:TAP01", "RQ1:TEMPMON:TAP01", 12),
                ("SIM:RQ1:TEMPMON:TAP24", "RQ1:TEMPMON:TAP24", 34),
                ("SIM:RQ1:TEMPMON:DCCT", "RQ1:TEMPMON:DCCT", 56),
                ("SIM:RQ2:TEMPMON:TAP01", "RQ2:TEMPMON:TAP01", 12),
                ("SIM:RQ2:TEMPMON:TAP36", "RQ2:TEMPMON:TAP36", 34),
                ("SIM:RQ2:TEMPMON:DCCT", "RQ2:TEMPMON:DCCT", 56),
                ("SIM:RB1:TEMPMON:TAP01", "RB1:TEMPMON:TAP01", 12),
                ("SIM:RB1:TEMPMON:TAP12", "RB1:TEMPMON:TAP12", 34),
                ("SIM:RB1:TEMPMON:DCCT", "RB1:TEMPMON:DCCT", 56),
            ]
        )
    )
    def test_GIVEN_temperature_monitoring_db_loaded_THEN_pvs_can_be_read(
        self, _, set_pv_name, get_pv_name, expected_value
    ):
        # Simple test to check that RIKENFE_TEMPMON.db loads successfully and a selection of PVs can be read

        self.ca.set_pv_value(set_pv_name, expected_value)
        self.ca.assert_that_pv_is(get_pv_name, expected_value)

    @parameterized.expand(
        [
            ("good_all_on", 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1),
            ("good_all_off", 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1),
            ("good_all_sweeping", 2, 2, 2, 2, 3, 3, 3, 1, 1, 1, 1),
            ("good_mixed", 2, 2, 2, 2, 4, 3, 1, 1, 1, 0, 0),
            ("good_fault", 2, 2, 2, 2, 4, 4, 4, 1, 1, 0, 0),
            ("bad_all_on", 1, 1, 1, 1, 2, 2, 2, 1, 0, 1, 0),
            ("bad_all_off", 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0),
            ("bad_all_sweeping", 1, 1, 1, 1, 3, 3, 3, 1, 0, 1, 0),
            ("bad_fault", 1, 1, 1, 1, 4, 4, 4, 1, 0, 0, 0),
            ("disconnected_all_on", 0, 0, 0, 0, 2, 2, 2, 1, 0, 1, 0),
            ("disconnected_all_off", 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0),
            ("disconnected_all_sweeping", 0, 0, 0, 0, 3, 3, 3, 1, 0, 1, 0),
            ("fault_all_on", 4, 4, 4, 4, 2, 2, 2, 1, 0, 1, 0),
            ("fault_all_off", 4, 4, 4, 4, 1, 1, 1, 1, 0, 1, 0),
            ("fault_all_sweeping", 4, 4, 4, 4, 3, 3, 3, 1, 0, 1, 0),
            ("warning_all_on", 3, 3, 3, 3, 2, 2, 2, 1, 0, 1, 0),
            ("warning_all_off", 3, 3, 3, 3, 1, 1, 1, 1, 0, 1, 0),
            ("warning_all_sweeping", 3, 3, 3, 3, 3, 3, 3, 1, 0, 1, 0),
            ("bad_mixed", 1, 1, 1, 1, 2, 3, 1, 1, 0, 1, 0),
            ("mixed_all_on", 1, 2, 3, 2, 2, 2, 2, 1, 0, 1, 0),
            ("mixed_all_off", 0, 1, 2, 3, 1, 1, 1, 1, 0, 1, 0),
            ("mixed_all_sweeping", 2, 3, 4, 0, 3, 3, 3, 1, 0, 1, 0),
        ]
    )
    def test_GIVEN_pumpsets_state_THEN_pumpset_summary_has_correct_state(
        self, _, gh1, gh2, gh3, gh4, tp, bp, piv, pumpset, gh_state, other_state, expected_state
    ):
        self.ca.set_pv_value(f"SIM:GH{(pumpset*4)-3}:STAT", gh1)
        self.ca.set_pv_value(f"SIM:GH{(pumpset*4)-2}:STAT", gh2)
        self.ca.set_pv_value(f"SIM:GH{(pumpset*4)-1}:STAT", gh3)
        self.ca.set_pv_value(f"SIM:GH{pumpset*4}:STAT", gh4)

        self.ca.assert_that_pv_is(f"PUMPSET:{pumpset}:GH", gh_state)

        self.ca.set_pv_value(f"SIM:TP{pumpset}:STAT", tp)
        self.ca.set_pv_value(f"SIM:PIV{pumpset}:STAT", bp)
        self.ca.set_pv_value(f"SIM:BP{pumpset}:STAT", piv)

        self.ca.assert_that_pv_is(f"PUMPSET:{pumpset}:OTHER", other_state)
        self.ca.assert_that_pv_is(f"PUMPSET:{pumpset}:STAT", expected_state)

    @parameterized.expand(
        [
            ("_all_on_no_interlock", 1, 1, 1, 2, 2, 2, 2, 2, "All On"),
            ("_all_off_no_interlock", 1, 1, 1, 1, 1, 1, 1, 1, "All Off"),
            ("_mixed_1_no_interlock", 1, 1, 1, 2, 1, 2, 2, 3, "Mixed State"),
            ("_mixed_2_no_interlock", 1, 1, 1, 1, 1, 1, 2, 3, "Mixed State"),
            ("_all_on_water", 4, 1, 1, 2, 2, 2, 2, 4, "Fault"),
            ("_all_off_water", 4, 1, 1, 1, 1, 1, 1, 4, "Fault"),
            ("_mixed_water", 4, 1, 1, 2, 1, 2, 2, 4, "Fault"),
            ("_all_on_vacuum", 1, 4, 1, 2, 2, 2, 2, 4, "Fault"),
            ("_all_off_vacuum", 1, 4, 1, 1, 1, 1, 1, 4, "Fault"),
            ("_mixed_vacuum", 1, 4, 1, 2, 1, 2, 2, 4, "Fault"),
            ("_all_on_mol", 1, 1, 4, 2, 2, 2, 2, 4, "Fault"),
            ("_all_off_mol", 1, 1, 4, 1, 1, 1, 1, 4, "Fault"),
            ("_mixed_mol", 1, 1, 4, 2, 1, 2, 2, 4, "Fault"),
            ("_comms_loss_in_interlock", 0, 1, 4, 2, 1, 2, 2, 0, "Comms Loss"),
            ("_comms_loss_in_power", 1, 1, 1, 2, 0, 2, 2, 0, "Comms Loss"),
        ]
    )
    def test_GIVEN_kicker_state_THEN_correct_summary(
        self, _, water, vacuum, mol, psu1, psu2, psu3, psu4, result, enum
    ):
        # Set interlocks
        self.ca.set_pv_value("SIM:KICKERS:WATER:ILK:STAT", water)
        self.ca.set_pv_value("SIM:KICKERS:VACUUM:ILK:STAT", vacuum)
        self.ca.set_pv_value("SIM:KICKERS:MOL:STAT", mol)

        # Set status
        self.ca.set_pv_value("SIM:KICKER1:PSU_ON:STAT", psu1)
        self.ca.set_pv_value("SIM:KICKER2:PSU_ON:STAT", psu2)
        self.ca.set_pv_value("SIM:KICKER3:PSU_ON:STAT", psu3)
        self.ca.set_pv_value("SIM:KICKER4:PSU_ON:STAT", psu4)

        # check states
        self.ca.assert_that_pv_is("KICKERS:SUMMARY:STAT", result)
        self.ca.assert_that_pv_is("KICKERS:SUMMARY:ENUM", enum)

    @parameterized.expand(parameterized_list([(0, 0, 0, 0), (1, 2, 3, 4), (4, 3, 2, 1)]))
    def test_GIVEN_current_THEN_correct_total(self, _, inpa, inpb, inpc, inpd):
        self.ca.set_pv_value("SIM:KICKER1:CURR", 0)
        self.ca.set_pv_value("SIM:KICKER2:CURR", 0)
        self.ca.set_pv_value("SIM:KICKER3:CURR", 0)
        self.ca.set_pv_value("SIM:KICKER4:CURR", 0)

        self.ca.set_pv_value("SIM:KICKER1:CURR", inpa)
        self.ca.assert_that_pv_is("KICKERS:CURRENT:TOTAL", inpa)
        self.ca.set_pv_value("SIM:KICKER2:CURR", inpb)
        self.ca.assert_that_pv_is("KICKERS:CURRENT:TOTAL", inpa + inpb)
        self.ca.set_pv_value("SIM:KICKER3:CURR", inpc)
        self.ca.assert_that_pv_is("KICKERS:CURRENT:TOTAL", inpa + inpb + inpc)
        self.ca.set_pv_value("SIM:KICKER4:CURR", inpd)
        self.ca.assert_that_pv_is("KICKERS:CURRENT:TOTAL", inpa + inpb + inpc + inpd)
