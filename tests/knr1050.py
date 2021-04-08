import unittest
from time import sleep

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

DEVICE_PREFIX = "KNR1050_01"

device_name = "knr1050"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KNR1050"),
        "macros": {},
        "emulator": device_name,
    },
]


TEST_MODES = [TestModes.DEVSIM]


class Knr1050Tests(unittest.TestCase):
    """
    Tests for the Knr1050 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(device_name, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0)
        self._lewis.backdoor_run_function_on_device("reset")
        # Set the device in remote mode ready to receive instructions
        self.ca.set_pv_value("MODE:SP", "REMOTE")
        self.ca.set_pv_value("MODE.PROC", 1)
        # Set the flow and concentrations to a default state that enable pump switch on
        self.ca.set_pv_value("STOP:SP", 1)
        self.ca.set_pv_value("STATUS", "OFF")
        self.ca.set_pv_value("FLOWRATE:SP", 0.01)
        self.ca.set_pv_value("PRESSURE:MIN:SP", 0)
        self.ca.set_pv_value("PRESSURE:MAX:SP", 100)
        self.ca.set_pv_value("COMP:A:SP", 100)
        self.ca.set_pv_value("COMP:B:SP", 0)
        self.ca.set_pv_value("COMP:C:SP", 0)
        self.ca.set_pv_value("COMP:D:SP", 0)
        self.ca.set_pv_value("STATUS:GET.PROC", 1)
        self.ca.set_pv_value("DISABLE:CHECK.PROC", 1)

    def _set_pressure_limit_low(self, limit):
        self._lewis.backdoor_set_on_device("pressure_limit_low", limit)

    def _set_pressure_limit_high(self, limit):
        self._lewis.backdoor_set_on_device("pressure_limit_high", limit)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_start_pump_sent_THEN_pump_starts(self):
        self.ca.set_pv_value("START:SP", 1)

        self.ca.assert_that_pv_is("STATUS", "IDLE")

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_timed_pump_sent_THEN_pump_starts(self):
        self.ca.set_pv_value("TIMED:SP", 1)

        self.ca.assert_that_pv_is("STATUS", "IDLE")

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_stop_pump_sent_via_ioc_THEN_device_state_off(self):
        expected_dev_state = "OFF"
        self.ca.set_pv_value("STOP:SP", 1)

        self.ca.assert_that_pv_is("STATUS", expected_dev_state)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_pump_is_turned_on_via_ioc_THEN_pump_is_on(self):
        self.ca.set_pv_value("START:SP", 1)
        pump_status = self._lewis.backdoor_get_from_device("pump_on")

        self.assertEqual(pump_status, True)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_concentration_via_ioc_WHEN_ramp_command_sent_via_ioc_THEN_correct_concentration_set(self):
        expected_concentrations = [0, 50, 35, 15]
        self.ca.set_pv_value("COMP:A:SP", expected_concentrations[0])
        self.ca.set_pv_value("COMP:B:SP", expected_concentrations[1])
        self.ca.set_pv_value("COMP:C:SP", expected_concentrations[2])
        self.ca.set_pv_value("COMP:D:SP", expected_concentrations[3])
        self.ca.set_pv_value("START:SP", 1)

        sleep(1.0) # allow emulator to process above data

        concentrations = [self.ca.get_pv_value("COMP:A"),
                          self.ca.get_pv_value("COMP:B"),
                          self.ca.get_pv_value("COMP:C"),
                          self.ca.get_pv_value("COMP:D")]
        self.assertEqual(expected_concentrations, concentrations)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_stop_pump_sent_THEN_lewis_pump_stops(self):
        expected_pump_status = False
        self.ca.set_pv_value("STOP:SP", 1)
        pump_status = self._lewis.backdoor_get_from_device("pump_on")

        self.assertEqual(pump_status, expected_pump_status)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_stop2_command_sent_THEN_expected_stop_type(self):
        self._lewis.backdoor_set_on_device("keep_last_values", False)
        stopped_status = self._lewis.backdoor_get_from_device("keep_last_values")
        self.assertEqual(stopped_status, False)
        self.ca.set_pv_value("_STOP:KLV:SP", 1)

        stopped_status = self._lewis.backdoor_get_from_device("keep_last_values")
        self.assertEqual(stopped_status, True)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_pump_switched_on_then_back_to_off_THEN_device_state_off(self):
        expected_dev_state = "OFF"
        self.ca.set_pv_value("START:SP", 1)
        self.ca.set_pv_value("STOP:SP", 1)

        sleep(1.0) # allow emulator to process above data

        state = self._lewis.backdoor_get_from_device("state")

        self.assertEqual(expected_dev_state, state)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_low_pressure_limit_via_backdoor_WHEN_get_low_pressure_limits_via_IOC_THEN_get_expected_pressure_limit(self):
        expected_pressure = 10
        self._set_pressure_limit_low(expected_pressure)
        self.ca.set_pv_value("PRESSURE:LIMITS.PROC", 1)

        self.ca.assert_that_pv_is("PRESSURE:MIN", expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_high_pressure_limit_via_backdoor_WHEN_get_high_pressure_limits_via_IOC_THEN_get_expected_pressure_limit(self):
        expected_pressure = 100
        self._set_pressure_limit_high(expected_pressure)
        self.ca.set_pv_value("PRESSURE:LIMITS.PROC", 1)

        self.ca.assert_that_pv_is("PRESSURE:MAX", expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_low_pressure_limit_via_ioc_WHEN_get_low_pressure_limit_THEN_get_expected_pressure_limit(self):
        expected_pressure = 10
        self.ca.set_pv_value("PRESSURE:MIN:SP", expected_pressure)
        self.ca.set_pv_value("PRESSURE:LIMITS.PROC", 1)
        self.ca.assert_that_pv_is("PRESSURE:MIN", expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_high_pressure_limit_via_ioc_WHEN_get_high_pressure_limit_via_backdoor_THEN_get_expected_pressure_limit(self):
        expected_pressure = 200
        self.ca.set_pv_value("PRESSURE:MAX:SP", expected_pressure)
        self.ca.set_pv_value("PRESSURE:LIMITS.PROC", 1)
        self.ca.assert_that_pv_is("PRESSURE:MAX", expected_pressure)

        self.assertEqual(self._lewis.backdoor_get_from_device("pressure_limit_high"), expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_low_pressure_limit_via_ioc_WHEN_get_low_pressure_limit_via_IOC_THEN_get_expected_value(self):
        expected_pressure = 45
        self.ca.set_pv_value("PRESSURE:MIN:SP", expected_pressure)
        self.ca.set_pv_value("PRESSURE:LIMITS.PROC", 1)
        self.ca.assert_that_pv_is("PRESSURE:MIN", expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_high_pressure_limit_via_ioc_WHEN_get_high_pressure_limit_via_IOC_THEN_get_expected_value(self):
        expected_pressure = 500

        self.ca.set_pv_value("PRESSURE:MAX:SP", expected_pressure)
        self.ca.set_pv_value("PRESSURE:LIMITS.PROC", 1)
        self.ca.assert_that_pv_is("PRESSURE:MAX", expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_flow_limit_min_via_ioc_WHEN_ramp_command_sent_via_IOC_THEN_correct_flow_limit_set(self):
        expected_flow = 0.01
        self.ca.set_pv_value("FLOWRATE:SP", expected_flow)
        self.ca.set_pv_value("START:SP", 1)

        self.ca.assert_that_pv_is("FLOWRATE", expected_flow)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_flow_limit_min_via_ioc_WHEN_get_flow_via_IOC_THEN_correct_flow_limit(self):
        expected_flow = 0.01
        self.ca.set_pv_value("FLOWRATE:SP", expected_flow)

        self.assertEqual(self.ca.get_pv_value("FLOWRATE:SP:RBV"), expected_flow)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_ioc_turned_on_WHEN_get_dev_state_via_ioc_THEN_off_state_returned(self):
        expected_dev_state = 'OFF'
        state = self.ca.get_pv_value("STATUS")

        self.assertEqual(expected_dev_state, state)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_ioc_turned_on_WHEN_set_local_mode_via_IOC_THEN_disabled_mode(self):
        expected_mode = 'Disabled'
        self.ca.set_pv_value("MODE:SP", "LOCAL")

        self.ca.assert_that_pv_is("DISABLE", expected_mode)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_local_mode_WHEN_set_pump_on_via_IOC_THEN_pump_disabled(self):
        self.ca.set_pv_value("MODE:SP", "LOCAL")
        self.ca.set_pv_value("START:SP", 1)

        self.ca.assert_that_pv_is("STATUS", 'OFF')

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_incorrect_gradients_WHEN_set_pump_on_via_IOC_THEN_pump_disabled(self):
        self.ca.set_pv_value("COMP:A:SP", 50)  # sum of gradients =/= 100%
        self.ca.set_pv_value("START:SP", 1)

        self.ca.assert_that_pv_is("STATUS", 'OFF')

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_get_status_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is('PRESSURE:LIMITS', ChannelAccess.Alarms.INVALID)

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_timed_run_started_THEN_remaining_time_decreases(self):
        self.ca.set_pv_value("TIME:SP", 10)
        self.ca.set_pv_value("TIMED:SP", 1)

        self.ca.assert_that_pv_value_is_decreasing("TIME:REMAINING", wait=5)

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_timed_run_started_THEN_pump_stopped_once_finished_run(self):
        self.ca.set_pv_value("TIME:SP", 10)
        self.ca.set_pv_value("TIMED:SP", 1)

        self.ca.assert_that_pv_is("STATUS", 'OFF', timeout=15)

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_long_timed_run_started_THEN_if_remaining_time_checked_then_not_finished(self):
        self.ca.set_pv_value("TIME:SP", 100)
        self.ca.set_pv_value("TIMED:SP", 1)

        self.ca.assert_that_pv_is("TIME:CHECK", 0)

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_set_volume_run_started_THEN_remaining_volume_decreases(self):
        self.ca.set_pv_value("FLOWRATE:SP", 0.02)
        self.ca.set_pv_value("VOL:SP", 0.05)
        self.ca.set_pv_value("TIMED:SP", 1)
        self.ca.assert_that_pv_is_not("VOL:REMAINING", 0.0, timeout=5)

        self.ca.assert_that_pv_value_is_decreasing("VOL:REMAINING", wait=5)

    @skip_if_recsim("Can't use lewis backdoor in RECSIM")
    def test_GIVEN_input_error_THEN_error_string_captured(self):
        expected_error = "20,Instrument in standalone mode"
        self._lewis.backdoor_set_on_device("input_correct", False)

        self.ca.assert_that_pv_is("ERROR:STR", expected_error, timeout=5)
