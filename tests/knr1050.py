import unittest

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


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


class Knr1050Tests(unittest.TestCase):
    """
    Tests for the Knr1050 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(device_name, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device("reset")
        # Set the device in remote mode ready to receive instructions
        self.ca.set_pv_value("REMOTE_MODE:SP", "Remote")
        self.ca.set_pv_value("GET_REMOTE_MODE.PROC", 1)
        # Set the flow and concentrations to a default state that enable pump switch on
        self.ca.set_pv_value("PUMP:STOP:SP", "Stop")
        self.ca.set_pv_value("DEV_STATE", "SYS_ST_OFF")
        self.ca.set_pv_value("FLOW:SP", 0.01)
        self.ca.set_pv_value("PRESS:LOW:SP", 0)
        self.ca.set_pv_value("PRESS:HIGH:SP", 100)
        self.ca.set_pv_value("CON:A:SP", 100)
        self.ca.set_pv_value("CON:B:SP", 0)
        self.ca.set_pv_value("CON:C:SP", 0)
        self.ca.set_pv_value("CON:D:SP", 0)
        self.ca.set_pv_value("GET_STATUS.PROC", 1)
        self.ca.set_pv_value("DISABLE:CHECK.PROC", 1)


    def _set_pressure_limit_low(self, limit):
        self._lewis.backdoor_set_on_device("pressure_limit_low", limit)

    def _set_pressure_limit_high(self, limit):
        self._lewis.backdoor_set_on_device("pressure_limit_high", limit)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_start_pump_sent_THEN_pump_starts(self):
        self.ca.set_pv_value("PUMP:START:SP", "Start")

        self.ca.assert_that_pv_is("DEV_STATE", "SYS_ST_IDLE")

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_stop_pump_sent_via_ioc_THEN_device_state_off(self):
        expected_dev_state = "SYS_ST_OFF"
        self.ca.set_pv_value("PUMP:STOP:SP", "Stop")

        self.ca.assert_that_pv_is("DEV_STATE", expected_dev_state)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_pump_is_turned_on_via_ioc_THEN_pump_is_on(self):
        self.ca.set_pv_value("PUMP:START:SP", "Start")
        pump_status = self._lewis.backdoor_get_from_device("pump_on")

        self.assertEqual(pump_status, "True")

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_concentration_via_ioc_WHEN_ramp_command_sent_via_ioc_THEN_correct_concentration_set(self):
        expected_concentrations = [0, 50, 35, 15]
        self.ca.set_pv_value("CON:A:SP", expected_concentrations[0])
        self.ca.set_pv_value("CON:B:SP", expected_concentrations[1])
        self.ca.set_pv_value("CON:C:SP", expected_concentrations[2])
        self.ca.set_pv_value("CON:D:SP", expected_concentrations[3])
        self.ca.set_pv_value("PUMP:START:SP", 1)

        concentrations = [self.ca.get_pv_value("CON:A"),
                          self.ca.get_pv_value("CON:B"),
                          self.ca.get_pv_value("CON:C"),
                          self.ca.get_pv_value("CON:D")]
        self.assertEqual(expected_concentrations, concentrations)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_stop_pump_sent_THEN_lewis_pump_stops(self):
        expected_pump_status = "False"
        self.ca.set_pv_value("PUMP:STOP:SP", "Stop")
        pump_status = self._lewis.backdoor_get_from_device("pump_on")

        self.assertEqual(pump_status, expected_pump_status)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_stop2_command_sent_THEN_expected_stop_type(self):
        self._lewis.backdoor_set_on_device("keep_last_values", "False")
        stopped_status = self._lewis.backdoor_get_from_device("keep_last_values")
        self.assertEqual(stopped_status, "False")
        self.ca.set_pv_value("_STOP:KLV:SP", 1)

        stopped_status = self._lewis.backdoor_get_from_device("keep_last_values")
        self.assertEqual(stopped_status, "True")

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_an_ioc_WHEN_pump_switched_on_then_back_to_off_THEN_device_state_off(self):
        expected_dev_state = "SYS_ST_OFF"
        self.ca.set_pv_value("PUMP:START:SP", "Start")
        self.ca.set_pv_value("PUMP:STOP:SP", "Stop")
        state = self._lewis.backdoor_get_from_device("state")

        self.assertEqual(expected_dev_state, state)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_low_pressure_limit_via_backdoor_WHEN_get_low_pressure_limits_via_IOC_THEN_get_expected_pressure_limit(self):
        expected_pressure = 10
        self._set_pressure_limit_low(expected_pressure)
        self.ca.set_pv_value("GET_PRESS:LIM.PROC", 1)

        self.ca.assert_that_pv_is("PRESS:LOW", expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_high_pressure_limit_via_backdoor_WHEN_get_high_pressure_limits_via_IOC_THEN_get_expected_pressure_limit(self):
        expected_pressure = 100
        self._set_pressure_limit_high(expected_pressure)
        self.ca.set_pv_value("GET_PRESS:LIM.PROC", 1)

        self.ca.assert_that_pv_is("PRESS:HIGH", expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_low_pressure_limit_via_ioc_WHEN_get_low_pressure_limit_THEN_get_expected_pressure_limit(self):
        expected_pressure = 10
        self.ca.set_pv_value("PRESS:LOW:SP", expected_pressure)
        self.ca.set_pv_value("GET_PRESS:LIM.PROC", 1)
        self.ca.assert_that_pv_is("PRESS:LOW", expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_high_pressure_limit_via_ioc_WHEN_get_high_pressure_limit_via_backdoor_THEN_get_expected_pressure_limit(self):
        expected_pressure = 200
        self.ca.set_pv_value("PRESS:HIGH:SP", expected_pressure)
        self.ca.set_pv_value("GET_PRESS:LIM.PROC", 1)
        self.ca.assert_that_pv_is("PRESS:HIGH", expected_pressure)

        self.assertEqual(int(self._lewis.backdoor_get_from_device("pressure_limit_high")), expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_low_pressure_limit_via_ioc_WHEN_get_low_pressure_limit_via_IOC_THEN_get_expected_value(self):
        expected_pressure = 45
        self.ca.set_pv_value("PRESS:LOW:SP", expected_pressure)
        self.ca.set_pv_value("GET_PRESS:LIM.PROC", 1)
        self.ca.assert_that_pv_is("PRESS:LOW", expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_high_pressure_limit_via_ioc_WHEN_get_high_pressure_limit_via_IOC_THEN_get_expected_value(self):
        expected_pressure = 500

        self.ca.set_pv_value("PRESS:HIGH:SP", expected_pressure)
        self.ca.set_pv_value("GET_PRESS:LIM.PROC", 1)
        self.ca.assert_that_pv_is("PRESS:HIGH", expected_pressure)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_flow_limit_min_via_ioc_WHEN_ramp_command_sent_via_IOC_THEN_correct_flow_limit_set(self):
        expected_flow = 0.01
        self.ca.set_pv_value("FLOW:SP", expected_flow)
        self.ca.set_pv_value("PUMP:START:SP", "Start")

        self.ca.assert_that_pv_is("FLOW", expected_flow)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_set_flow_limit_min_via_ioc_WHEN_get_flow_via_IOC_THEN_correct_flow_limit(self):
        expected_flow = 0.01
        self.ca.set_pv_value("FLOW:SP", expected_flow)

        self.assertEqual(self.ca.get_pv_value("FLOW"), expected_flow)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_ioc_turned_on_WHEN_get_dev_state_via_ioc_THEN_off_state_returned(self):
        expected_dev_state = 'SYS_ST_OFF'
        state = self.ca.get_pv_value("DEV_STATE")

        self.assertEqual(expected_dev_state, state)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_ioc_turned_on_WHEN_set_local_mode_via_IOC_THEN_disabled_mode(self):
        expected_mode = 'Disabled'
        self.ca.set_pv_value("LOCAL_MODE:SP", "Local")

        self.ca.assert_that_pv_is("DISABLE", expected_mode)

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_local_mode_WHEN_set_pump_on_via_IOC_THEN_pump_disabled(self):
        self.ca.set_pv_value("LOCAL_MODE:SP", "Local")
        self.ca.set_pv_value("PUMP:START:SP", "Start")

        self.ca.assert_that_pv_is("DEV_STATE", 'SYS_ST_OFF')

    @skip_if_recsim("Recsim simulation not implemented")
    def test_GIVEN_incorrect_gradients_WHEN_set_pump_on_via_IOC_THEN_pump_disabled(self):
        self.ca.set_pv_value("CON:A:SP", 50)  # sum of gradients =/= 100%
        self.ca.set_pv_value("PUMP:START:SP", "Start")

        self.ca.assert_that_pv_is("DEV_STATE", 'SYS_ST_OFF')

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_get_status_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is('GET_REMOTE_MODE', ChannelAccess.Alarms.INVALID)
