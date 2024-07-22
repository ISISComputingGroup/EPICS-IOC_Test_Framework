import os
import unittest

from parameterized import parameterized

from utils.build_architectures import BuildArchitectures
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP, IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes

IOCS = [
    {
        "name": "FINS_01",
        "directory": get_default_ioc_dir("FINS"),
        "custom_prefix": "FINS_VAC",
        "pv_for_existence": "HEARTBEAT",
        "macros": {
            "FINSCONFIGDIR": (
                os.path.join(EPICS_TOP, "ioc", "master", "FINS", "exampleSettings", "SANS2D_vacuum")
            ).replace("\\", "/"),
            "PLCIP": "127.0.0.1",
        },
    },
    {
        "name": "RUNCTRL_01",
        "directory": (
            os.path.join(EPICS_TOP, "ioc", "master", "RUNCTRL", "iocBoot", "iocRUNCTRL_01")
        ).replace("\\", "/"),
        "custom_prefix": "CS:IOC:RUNCTRL_01",
        "pv_for_existence": "DEVIOS:HEARTBEAT",
    },
    {
        "name": "ISISDAE_01",
        "directory": get_default_ioc_dir("ISISDAE"),
        "custom_prefix": "CS:IOC:ISISDAE_01",
        "pv_for_existence": "DEVIOS:HEARTBEAT",
    },
]


TEST_MODES = [TestModes.RECSIM]
BUILD_ARCHITECTURES = [BuildArchitectures._64BIT]


class Sans2dVacuumSystemTests(unittest.TestCase):
    """
    Tests for the SANS2D vacuum system, based on a FINS PLC.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running("FINS_01")
        self.ca = ChannelAccess(device_prefix="FINS_VAC")

    def test_WHEN_ioc_is_run_THEN_heartbeat_record_exists(self):
        self.ca.assert_setting_setpoint_sets_readback(1, "HEARTBEAT", "SIM:HEARTBEAT")

    @parameterized.expand(
        [
            (1, "IN", ChannelAccess.Alarms.NONE),
            (2, "OUT", ChannelAccess.Alarms.NONE),
            (3, "UNKNOWN", ChannelAccess.Alarms.MAJOR),
            (4, "ERROR", ChannelAccess.Alarms.MAJOR),
            (5, "ERROR(IN)", ChannelAccess.Alarms.MAJOR),
            (6, "ERROR(OUT)", ChannelAccess.Alarms.MAJOR),
        ]
    )
    def test_WHEN_data_changes_THEN_monitor_status_correct(self, raw_value, enum_string, alarm):
        self.ca.set_pv_value("SIM:ADDR:1001", raw_value)
        self.ca.assert_that_pv_is("MONITOR3:STATUS", enum_string)
        self.ca.assert_that_pv_alarm_is("MONITOR3:STATUS", alarm)

    @parameterized.expand(
        [
            (7, "CLOSED", ChannelAccess.Alarms.NONE),
            (8, "OPEN", ChannelAccess.Alarms.NONE),
            (16, "ERROR", ChannelAccess.Alarms.MAJOR),
            (24, "ERROR(OPEN)", ChannelAccess.Alarms.MAJOR),
        ]
    )
    def test_WHEN_data_changes_THEN_shutter_status_correct(self, raw_value, enum_string, alarm):
        self.ca.set_pv_value("SIM:ADDR:1001", raw_value)
        self.ca.assert_that_pv_is("SHUTTER:STATUS", enum_string)
        self.ca.assert_that_pv_alarm_is("SHUTTER:STATUS", alarm)

    @parameterized.expand(
        [
            (127, "CLOSED", ChannelAccess.Alarms.NONE),
            (128, "OPEN", ChannelAccess.Alarms.NONE),
            (256, "ERROR", ChannelAccess.Alarms.MAJOR),
            (384, "ERROR(OPEN)", ChannelAccess.Alarms.MAJOR),
        ]
    )
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

    @parameterized.expand(
        [
            (1, "DEFLATED", ChannelAccess.Alarms.NONE),
            (2, "INFLATING", ChannelAccess.Alarms.NONE),
            (4, "INFLATED", ChannelAccess.Alarms.NONE),
            (8, "DEFLATING", ChannelAccess.Alarms.NONE),
        ]
    )
    def test_WHEN_data_changes_THEN_seal_status_correct(self, raw_value, enum_string, alarm):
        self.ca.set_pv_value("SIM:ADDR:1004", raw_value)
        self.ca.assert_that_pv_is("SEAL:STATUS", enum_string)
        self.ca.assert_that_pv_alarm_is("SEAL:STATUS", alarm)

    @parameterized.expand([(0, 0), (4000, 10000), (2000, 5000)])
    def test_WHEN_seal_supply_pressure_changes_THEN_correctly_converted(
        self, raw_value, expected_converted_val
    ):
        self.ca.set_pv_value("SIM:SEAL:SUPPLY:PRESS:RAW", raw_value)
        self.ca.assert_that_pv_is("SEAL:SUPPLY:PRESS", expected_converted_val)

    def _set_sp_and_assert(self, set_pv, state, expected_state=None, int_state=None):
        if int_state is None:
            int_state = state
        if expected_state is None:
            expected_state = state
        self.ca.set_pv_value("{}:STATUS:SP".format(set_pv), int_state)
        self.ca.assert_that_pv_monitor_gets_values(
            "{}:{}:SP".format(set_pv, expected_state), [expected_state, "..."]
        )

    def test_WHEN_opening_and_closing_shutter_THEN_propogates(self):
        self._set_sp_and_assert("SHUTTER", "OPEN")
        self._set_sp_and_assert("SHUTTER", "CLOSE")
        self._set_sp_and_assert("SHUTTER", "OPEN")

    def test_WHEN_opening_and_closing_shutter_with_numbers_THEN_propogates(self):
        self._set_sp_and_assert("SHUTTER", "OPEN", 1)
        self._set_sp_and_assert("SHUTTER", "CLOSE", 0)
        self._set_sp_and_assert("SHUTTER", "OPEN", 1)

    def set_test_detector_limits(self, ca, record, current, high):
        # the value of record is updated by writing to rec_sim when SIMM is enabled
        rec_sim = "SIM:" + record
        ca.assert_setting_setpoint_sets_readback("YES", record + ".SIMM", record + ".SIMM")
        rec_enable = record + ":DC:ENABLE"
        rec_high = record + ":DC:HIGH"
        rec_inrang = record + ":DC:INRANGE"
        ca.assert_setting_setpoint_sets_readback("NO", rec_enable, rec_enable)
        ca.assert_setting_setpoint_sets_readback(0, record, rec_sim)
        ca.assert_setting_setpoint_sets_readback(high, rec_high, rec_high)
        ca.assert_setting_setpoint_sets_readback("YES", rec_enable, rec_enable)
        ca.assert_setting_setpoint_sets_readback("YES", rec_inrang, rec_inrang)
        ca.assert_setting_setpoint_sets_readback(current, record, rec_sim)
        ca.assert_that_pv_is(rec_inrang, "NO")

    def reset_detector_limits(self, ca, record):
        rec_enable = record + ":DC:ENABLE"
        ca.assert_setting_setpoint_sets_readback("NO", rec_enable, rec_enable)
        ca.assert_setting_setpoint_sets_readback("NO", record + ".SIMM", record + ".SIMM")

    def test_WHEN_detector_rate_exceeded_THEN_shutter_closes(self):
        for detector, record in (
            ("AD1", "INTG:RATE"),
            ("AD1", "INTG:SPEC:RATE"),
            ("AD2", "INTG:RATE"),
            ("AD2", "INTG:SPEC:RATE"),
        ):
            ca_dae = ChannelAccess(device_prefix="DAE:" + detector)
            self._set_sp_and_assert("SHUTTER", "OPEN")
            self.set_test_detector_limits(ca_dae, record, 20, 10)
            self.ca.set_pv_value("SHUTTER:STATUS", "CLOSED")
            self.reset_detector_limits(ca_dae, record)

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
