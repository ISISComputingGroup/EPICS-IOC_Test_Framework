import unittest
import os

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir, EPICS_TOP
from parameterized import parameterized

from utils.test_modes import TestModes
from utils.testing import parameterized_list

ioc_name = "FINS"
test_path = os.path.join(EPICS_TOP, "ioc", "master", ioc_name, "exampleSettings", "SANS2D_vacuum")
ioc_prefix = "FINS_VAC"

IOCS = [
    {
        "name": "FINS_01",
        "directory": get_default_ioc_dir(ioc_name),
        "custom_prefix": ioc_prefix,
        "pv_for_existence": "HEARTBEAT",
        "macros": {
            "FINSCONFIGDIR": test_path.replace("\\", "/"),
            "PLCIP": "127.0.0.1"
        },
    },
]


TEST_MODES = [TestModes.RECSIM]


class Sans2dVacuumSystemTests(unittest.TestCase):
    """
    Tests for the SANS2D vacuum system, based on a FINS PLC.
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("FINS_01")
        self.ca = ChannelAccess(device_prefix=ioc_prefix)

    def test_WHEN_ioc_is_run_THEN_heartbeat_record_exists(self):
        self.ca.assert_setting_setpoint_sets_readback(1, "HEARTBEAT", "SIM:HEARTBEAT")

    @parameterized.expand([(1, "IN", ChannelAccess.Alarms.NONE),
                           (2, "OUT", ChannelAccess.Alarms.NONE),
                           (3, "UNKNOWN", ChannelAccess.Alarms.MAJOR),
                           (4, "ERROR", ChannelAccess.Alarms.MAJOR),
                           (5, "ERROR(IN)", ChannelAccess.Alarms.MAJOR),
                           (6, "ERROR(OUT)", ChannelAccess.Alarms.MAJOR)])
    def test_WHEN_data_changes_THEN_monitor_status_correct(self, raw_value, enum_string, alarm):
        self.ca.set_pv_value("SIM:ADDR:1001", raw_value)
        self.ca.assert_that_pv_is("MONITOR3:STATUS", enum_string)
        self.ca.assert_that_pv_alarm_is("MONITOR3:STATUS", alarm)

    @parameterized.expand([(7, "CLOSED", ChannelAccess.Alarms.NONE),
                           (8, "OPEN", ChannelAccess.Alarms.NONE),
                           (16, "ERROR", ChannelAccess.Alarms.MAJOR),
                           (24, "ERROR(OPEN)", ChannelAccess.Alarms.MAJOR)])
    def test_WHEN_data_changes_THEN_shutter_status_correct(self, raw_value, enum_string, alarm):
        self.ca.set_pv_value("SIM:ADDR:1001", raw_value)
        self.ca.assert_that_pv_is("SHUTTER:STATUS", enum_string)
        self.ca.assert_that_pv_alarm_is("SHUTTER:STATUS", alarm)

    @parameterized.expand([(127, "CLOSED", ChannelAccess.Alarms.NONE),
                           (128, "OPEN", ChannelAccess.Alarms.NONE),
                           (256, "ERROR", ChannelAccess.Alarms.MAJOR),
                           (384, "ERROR(OPEN)", ChannelAccess.Alarms.MAJOR)])
    def test_WHEN_data_changes_THEN_v8_status_correct(self, raw_value, enum_string, alarm):
        self.ca.set_pv_value("SIM:ADDR:1001", raw_value)
        self.ca.assert_that_pv_is("V8:STATUS", enum_string)
        self.ca.assert_that_pv_alarm_is("V8:STATUS", alarm)

    def test_WHEN_common_alarm_low_THEN_common_alarm_bad_high_and_alarm(self):
        self.ca.set_pv_value("SIM:ADDR:1001", 0)
        self.ca.assert_that_pv_is("COMMON_ALARM:BAD", 1)
        self.ca.assert_that_pv_alarm_is("COMMON_ALARM:BAD", ChannelAccess.Alarms.MAJOR)

    def test_WHEN_common_alarm_high_THEN_common_alarm_bad_low_and_no_alarm(self):
        self.ca.set_pv_value("SIM:ADDR:1001", 32768)
        self.ca.assert_that_pv_is("COMMON_ALARM:BAD", 0)
        self.ca.assert_that_pv_alarm_is("COMMON_ALARM:BAD", ChannelAccess.Alarms.NONE)

    @parameterized.expand([(1, "DEFLATED", ChannelAccess.Alarms.NONE),
                           (2, "INFLATING", ChannelAccess.Alarms.NONE),
                           (4, "INFLATED", ChannelAccess.Alarms.NONE),
                           (8, "DEFLATING", ChannelAccess.Alarms.NONE)])
    def test_WHEN_data_changes_THEN_seal_status_correct(self, raw_value, enum_string, alarm):
        self.ca.set_pv_value("SIM:ADDR:1004", raw_value)
        self.ca.assert_that_pv_is("SEAL:STATUS", enum_string)
        self.ca.assert_that_pv_alarm_is("SEAL:STATUS", alarm)

    @parameterized.expand([(0, 0),
                           (4000, 10000),
                           (2000, 5000)])
    def test_WHEN_seal_supply_pressure_changes_THEN_correctly_converted(self, raw_value, expected_converted_val):
        self.ca.set_pv_value("SIM:SEAL:SUPPLY:PRESS:RAW", raw_value)
        self.ca.assert_that_pv_is("SEAL:SUPPLY:PRESS", expected_converted_val)

    def _set_sp_and_assert(self, set_pv, state, expected_state=None, int_state=None):
        if int_state is None:
            int_state = state
        if expected_state is None:
            expected_state = state
        self.ca.set_pv_value("{}:STATUS:SP".format(set_pv), int_state)
        self.ca.assert_that_pv_monitor_gets_values("{}:{}:SP".format(set_pv, expected_state), [expected_state, "..."])

    def test_WHEN_opening_and_closing_shutter_THEN_propogates(self):
        self._set_sp_and_assert("SHUTTER", "OPEN")
        self._set_sp_and_assert("SHUTTER", "CLOSE")
        self._set_sp_and_assert("SHUTTER", "OPEN")

    def test_WHEN_opening_and_closing_shutter_with_numbers_THEN_propogates(self):
        self._set_sp_and_assert("SHUTTER", "OPEN", 1)
        self._set_sp_and_assert("SHUTTER", "CLOSE", 0)
        self._set_sp_and_assert("SHUTTER", "OPEN", 1)

    def test_WHEN_insert_and_extract_monitor_THEN_propogates(self):
        self._set_sp_and_assert("MONITOR3", "IN", "INSERT")
        self._set_sp_and_assert("MONITOR3", "OUT", "EXTRACT")
        self._set_sp_and_assert("MONITOR3", "IN", "INSERT")

    def test_WHEN_insert_and_extract_monitor_with_numbers_THEN_propogates(self):
        self._set_sp_and_assert("MONITOR3", "IN", "INSERT", 1)
        self._set_sp_and_assert("MONITOR3", "OUT", "EXTRACT", 0)
        self._set_sp_and_assert("MONITOR3", "IN", "INSERT", 1)

    def test_WHEN_start_and_stop_guide_THEN_propogates(self):
        self._set_sp_and_assert("GUIDE", "START")
        self._set_sp_and_assert("GUIDE", "STOP")
        self._set_sp_and_assert("GUIDE", "START")

    def test_WHEN_start_and_stop_guide_with_numbers_THEN_propogates(self):
        self._set_sp_and_assert("GUIDE", "START", 1)
        self._set_sp_and_assert("GUIDE", "STOP", 0)
        self._set_sp_and_assert("GUIDE", "START", 1)

    def test_WHEN_begin_run_in_auto_shutter_mode_THEN_shutter_opened(self):
        self.ca.set_pv_value("SHUTTER:STATUS:SP", "CLOSE", wait=True)
        self.ca.set_pv_value("SHUTTER:AUTO", 1, wait=True)

        self.ca.process_pv("SHUTTER:OPEN_IF_AUTO")

        self.ca.assert_that_pv_is("SHUTTER:STATUS:SP", "OPEN")

    def test_WHEN_begin_run_in_manual_shutter_mode_THEN_shutter_opened(self):
        self.ca.set_pv_value("SHUTTER:STATUS:SP", "CLOSE", wait=True)
        self.ca.set_pv_value("SHUTTER:AUTO", 0, wait=True)

        self.ca.process_pv("SHUTTER:OPEN_IF_AUTO")

        self.ca.assert_that_pv_is_not("SHUTTER:STATUS:SP", "OPEN", timeout=5)

    def test_WHEN_end_run_in_auto_shutter_mode_THEN_shutter_opened(self):
        self.ca.set_pv_value("SHUTTER:STATUS:SP", "OPEN", wait=True)
        self.ca.set_pv_value("SHUTTER:AUTO", 1, wait=True)

        self.ca.process_pv("SHUTTER:CLOSE_IF_AUTO")

        self.ca.assert_that_pv_is("SHUTTER:STATUS:SP", "CLOSE")

    def test_WHEN_end_run_in_manual_shutter_mode_THEN_shutter_opened(self):
        self.ca.set_pv_value("SHUTTER:STATUS:SP", "OPEN", wait=True)
        self.ca.set_pv_value("SHUTTER:AUTO", 0, wait=True)

        self.ca.process_pv("SHUTTER:CLOSE_IF_AUTO")

        self.ca.assert_that_pv_is_not("SHUTTER:STATUS:SP", "CLOSE", timeout=5)


class Sans2dVacuumTankTest(unittest.TestCase):
    """
    Tests for the SANS2D vacuum tank, based on a FINS PLC.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running("FINS_01")
        self.ca = ChannelAccess(device_prefix=ioc_prefix)

    @parameterized.expand(parameterized_list([-5, 0, 3, 5, 7, 9, 16]))
    def test_WHEN_set_tank_status_to_unknown_value_THEN_error_status(self, _, status_rval):
        self.ca.set_pv_value("SIM:TANK:STATUS", status_rval)
        self.ca.assert_that_pv_is("TANK:STATUS", "ERROR: STATUS UNKNOWN")
        self.ca.assert_that_pv_alarm_is("TANK:STATUS", "MAJOR")

    @parameterized.expand([(1, "ATMOSPHERE"), (2, "VAC DOWN"), (4, "AT VACUUM"), (8, "VENTING")])
    def test_WHEN_set_tank_status_to_known_value_THEN_no_error(self, status_rval, status_val):
        self.ca.set_pv_value("SIM:TANK:STATUS", status_rval)
        self.ca.assert_that_pv_is("TANK:STATUS", status_val)
        self.ca.assert_that_pv_alarm_is("TANK:STATUS", "NO_ALARM")
