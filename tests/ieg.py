import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

from time import sleep


class IegTests(unittest.TestCase):
    """
    Tests for the IEG IOC.
    """

    operation_modes = [(1, "Pump, Purge & Fill"),
                       (2, "Pump"),
                       (3, "Gas Flow"),
                       (4, "Gas - Single Shot"),]

    error_codes = [(0, "No error"),
                   (2, "Samp vol: leak detected"),
                   (3, "Samp vol: no vacuum"),
                   (4, "Samp vol: pump timeout"),
                   (5, "Buff vol: did not fill"),
                   (6, "Samp vol: fill iterations"),
                   (7, "Samp vol: fill timeout"),
                   (8, "Buff or samp vol leak"),
                   (9, "Shot didn't raise press."),
                   (10, "Manual stop"),
                   (11, "Vacuum tank interlock"),
                   (12, "Samp vol: leak detected"),
                   (13, "Sensor broken/disconnect")]

    test_device_ids = [0, 123, 255]

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("ieg")

        self.ca = ChannelAccess(20)
        self.ca.wait_for("IEG_01:DISABLE", timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("IEG_01:DISABLE", "COMMS ENABLED")

    @skipIf(IOCRegister.uses_rec_sim, "Recsim not implemented yet")
    def test_WHEN_mode_setpoint_is_set_THEN_readback_updates(self):
        for set_val, return_val in self.operation_modes:
            self.ca.assert_setting_setpoint_sets_readback(set_val, set_point_pv="IEG_01:MODE:SP", readback_pv="IEG_01:MODE", expected_value=return_val)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_device_id_is_changed_on_device_THEN_device_id_pv_updates(self):
        for val in self.test_device_ids:
            self._lewis.backdoor_set_on_device("unique_id", val)
            self.ca.assert_that_pv_is("IEG_01:ID", val, timeout=30)
            self.ca.assert_pv_alarm_is("IEG_01:ID", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_valve_states_are_changed_on_device_THEN_valve_state_pv_updates(self):
        for gas_valve_state in [True, False]:
            self._lewis.backdoor_set_on_device("gas_valve_open", gas_valve_state)
            for buffer_valve_state in [True, False]:
                self._lewis.backdoor_set_on_device("buffer_valve_open", buffer_valve_state)
                for pump_valve_state in [True, False]:
                    self._lewis.backdoor_set_on_device("pump_valve_open", pump_valve_state)
                    self.ca.assert_that_pv_is_number("IEG_01:VALVESTATE.B0", 1 if pump_valve_state is True else 0)
                    self.ca.assert_that_pv_is_number("IEG_01:VALVESTATE.B1", 1 if buffer_valve_state is True else 0)
                    self.ca.assert_that_pv_is_number("IEG_01:VALVESTATE.B2", 1 if gas_valve_state is True else 0)
                    self.ca.assert_pv_alarm_is("IEG_01:VALVESTATE", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_valve_states_are_changed_on_device_THEN_valve_state_pv_updates(self):
        for error_num, error in self.error_codes:
            self._lewis.backdoor_set_on_device("error", error_num)
            self.ca.assert_that_pv_is("IEG_01:ERROR", error)
            self.ca.assert_pv_alarm_is("IEG_01:ERROR", self.ca.ALARM_NONE)