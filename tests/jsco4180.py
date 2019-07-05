import unittest
from time import sleep

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "JSCO4180_01"
DEVICE_NAME = "jsco4180"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("JSCO4180"),
        "macros": {},
        "emulator": DEVICE_NAME,
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Jsco4180Tests(unittest.TestCase):
    """
    Tests for the Jsco4180 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("FLOWRATE", timeout=30)
        self._lewis.backdoor_run_function_on_device("reset")
        self.resetIocRecords()

    def resetIocRecords(self):
        self.ca.set_pv_value("TIME", 0)
        self.ca.set_pv_value("TIME:CALC:SP", "Time")
        self.ca.set_pv_value("TIME:RUN:SP", 60)
        self.ca.set_pv_value("TIME:MODE", "STOPPED")
        self.ca.set_pv_value("FLOWRATE:SP", 0.010)
        self.ca.set_pv_value("FLOWRATE", 0.000)
        self.ca.set_pv_value("PRESSURE", 0)
        self.ca.set_pv_value("PRESSURE:MAX:SP", 400)
        self.ca.set_pv_value("PRESSURE:MIN:SP", 1)
        self.ca.set_pv_value("TIME:RUN:SP", 60)
        self.ca.set_pv_value("COMP:A", 100)
        self.ca.set_pv_value("COMP:A:SP", 100)
        self.ca.set_pv_value("COMP:B", 0)
        self.ca.set_pv_value("COMP:B:SP", 0)
        self.ca.set_pv_value("COMP:C", 0)
        self.ca.set_pv_value("COMP:C:SP", 0)
        self.ca.set_pv_value("COMP:D", 0)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_wrong_component_on_device_WHEN_running_THEN_retry_run_and_updates_component(self):
        expected_value = 50
        self.ca.set_pv_value("COMP:A:SP", expected_value)
        self.ca.set_pv_value("COMP:B:SP", expected_value)

        self.ca.set_pv_value("START:SP", 1)

        # Setting an incorrect component on the device will result in the state machine attempting
        # to rerun the pump and reset components.
        self._lewis.backdoor_set_on_device("component_A", 33)

        sleep(5)

        self.ca.assert_that_pv_is("COMP:A", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_device_in_single_channel_mode_WHEN_running_THEN_pump_stops_and_errors(self):
        self._lewis.backdoor_set_on_device("single_channel_mode", True)
        expected_status = "STOPPED"
        expected_error = "Single Channel"
        self.ca.set_pv_value("COMP:A:SP", 50)
        self.ca.set_pv_value("COMP:C:SP", 50)

        self.ca.set_pv_value("START:SP", 1)

        # Give the state machine some time to attempt 4 restarts
        sleep(30)

        self.ca.assert_that_pv_is("STATUS", expected_status)
        self.ca.assert_that_pv_is("ERROR:COMP", expected_error)

    @skip_if_recsim("Flowrate device logic not supported in RECSIM")
    def test_GIVEN_an_ioc_WHEN_set_flowrate_THEN_flowrate_setpoint_is_correct(self):
        expected_value = 1.000
        self.ca.set_pv_value("FLOWRATE:SP", expected_value)

        self.ca.assert_that_pv_is("FLOWRATE:SP:RBV", expected_value)

        self.ca.set_pv_value("START:SP", 1)
        self.ca.assert_that_pv_is("FLOWRATE", expected_value)

    @skip_if_recsim("Lewis device logic not supported in RECSIM")
    def test_GIVEN_an_ioc_WHEN_set_maximum_pressure_limit_THEN_maximum_pressure_limit_is_correct(self):
        expected_value = 200
        self.ca.set_pv_value("PRESSURE:MAX:SP", expected_value)

        self.ca.assert_that_pv_is("PRESSURE:MAX", expected_value)

    @skip_if_recsim("Lewis device logic not supported in RECSIM")
    def test_GIVEN_an_ioc_WHEN_set_minimum_pressure_limit_THEN_minimum_pressure_limit_is_correct(self):
        expected_value = 100
        self.ca.set_pv_value("PRESSURE:MIN:SP", expected_value)

        self.ca.assert_that_pv_is("PRESSURE:MIN", expected_value)

    def test_GIVEN_an_ioc_WHEN_continuous_pump_set_THEN_pump_on(self):
        self.ca.set_pv_value("START:SP", 1)

        self.ca.assert_that_pv_is("TIME:MODE", "CONTINUOUS")

    def test_GIVEN_an_ioc_WHEN_timed_pump_set_THEN_timed_pump_on(self):
        # Set a run time for a timed run
        self.ca.set_pv_value("TIME:RUN:SP", 10000)
        self.ca.set_pv_value("TIMED:SP", 1)

        self.ca.assert_that_pv_is("TIME:MODE", "TIMED")

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_an_ioc_WHEN_get_current_pressure_THEN_current_pressure_returned(self):
        expected_value = 300
        self._lewis.backdoor_set_on_device("pressure", expected_value)

        self.ca.assert_that_pv_is("PRESSURE", expected_value)

    @parameterized.expand([
        ("component_{}".format(suffix), suffix) for suffix in ["A", "B", "C", "D"]
    ])
    @skip_if_recsim("Reliant on setUP lewis backdoor call")
    def test_GIVEN_an_ioc_WHEN_get_component_THEN_correct_component_returned(self, component, suffix):
        expected_value = 10.0
        self._lewis.backdoor_set_on_device(component, expected_value)

        self.ca.assert_that_pv_is("COMP:{}".format(suffix), expected_value)

    @parameterized.expand([
        ("COMP:{}".format(suffix), suffix) for suffix in ["A", "B", "C"]
    ])
    @skip_if_recsim("Reliant on setUP lewis backdoor call")
    def test_GIVEN_an_ioc_WHEN_set_component_THEN_correct_component_set(self, component, suffix):
        expected_value = 100.0
        self.ca.set_pv_value("COMP:{}:SP".format(suffix), expected_value)
        # Call the hidden function rather than the normal full sequence (START:SP) as we are testing this
        # specific set composition record
        self.ca.set_pv_value("COMP:SP", "Set")

        self.ca.assert_that_pv_is(component, expected_value)

    def test_GIVEN_ioc_initial_state_WHEN_get_error_THEN_error_returned(self):
        expected_value = "No error"

        self.ca.assert_that_pv_is("ERROR", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_ioc_in_error_state_WHEN_get_error_THEN_error_returned(self):
        expected_value = "Hardware error"
        self._lewis.backdoor_set_on_device("error", 4)

        self.ca.assert_that_pv_is("ERROR", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_ioc_in_error_state_WHEN_reset_error_THEN_error_reset(self):
        expected_value = "No error"
        self._lewis.backdoor_set_on_device("error", 2)
        self.ca.set_pv_value("ERROR:SP", "Reset")

        self.ca.assert_that_pv_is("ERROR", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_ioc_in_error_state_WHEN_reset_error_THEN_error_reset(self):
        expected_value = "No error"
        self._lewis.backdoor_set_on_device("error", 4)

        self.ca.assert_that_pv_is("ERROR", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_device_not_connected_WHEN_get_error_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is('ERROR:SP', ChannelAccess.Alarms.INVALID, timeout=2)

    @skip_if_recsim("Reliant on setUP lewis backdoor call")
    def test_GIVEN_timed_pump_WHEN_get_program_runtime_THEN_program_runtime_increments(self):
        self.ca.set_pv_value("TIME:RUN:SP", 10000)
        self.ca.set_pv_value("TIMED:SP", 1)

        self.ca.assert_that_pv_value_is_increasing("TIME", wait=2)

    def test_GIVEN_timed_pump_WHEN_set_constant_pump_THEN_state_updated_to_constant_pump(self):
        # Set a run time for a timed run
        self.ca.set_pv_value("TIME:RUN:SP", 10000)
        self.ca.set_pv_value("TIMED:SP.PROC", 1)
        expected_value = "TIMED"
        self.ca.assert_that_pv_is("TIME:MODE", expected_value)

        self.ca.set_pv_value("START:SP", 1)
        expected_value = "CONTINUOUS"
        self.ca.assert_that_pv_is("TIME:MODE", expected_value)

    def test_GIVEN_constant_pump_WHEN_set_timed_pump_THEN_state_updated_to_timed_pump(self):
        self.ca.set_pv_value("START:SP", 1)
        expected_value = "CONTINUOUS"
        self.ca.assert_that_pv_is("TIME:MODE", expected_value)

        # Set a run time for a timed run
        self.ca.set_pv_value("TIME:RUN:SP", 10000)
        self.ca.set_pv_value("TIMED:SP", 1)
        expected_value = "TIMED"
        self.ca.assert_that_pv_is("TIME:MODE", expected_value)

    def test_GIVEN_calc_mode_is_time_WHEN_setting_time_THEN_time_and_volume_are_correctly_set(self):
        expected_time = 600
        expected_volume = 0.1
        self.ca.set_pv_value("TIME:CALC:SP", "Time")

        self.ca.set_pv_value("TIME:RUN:SP", expected_time)

        self.ca.assert_that_pv_is("TIME:RUN:SP", expected_time)
        self.ca.assert_that_pv_is("TIME:VOL:SP", expected_volume)

    def test_GIVEN_calc_mode_is_time_WHEN_setting_volume_THEN_set_is_ignored(self):
        expected_time = self.ca.get_pv_value("TIME:RUN:SP")
        expected_volume = self.ca.get_pv_value("TIME:VOL:SP")
        self.ca.set_pv_value("TIME:CALC:SP", "Time")

        self.ca.set_pv_value("TIME:VOL:SP", expected_volume * 10)

        self.ca.assert_that_pv_is("TIME:RUN:SP", expected_time)
        self.ca.assert_that_pv_is("TIME:VOL:SP", expected_volume)

    def test_GIVEN_calc_mode_is_volume_WHEN_setting_volume_THEN_time_and_volume_are_correctly_set(self):
        expected_time = 600
        expected_volume = 0.1
        self.ca.set_pv_value("TIME:CALC:SP", "Volume")

        self.ca.set_pv_value("TIME:VOL:SP", expected_volume)

        self.ca.assert_that_pv_is("TIME:RUN:SP", expected_time)
        self.ca.assert_that_pv_is("TIME:VOL:SP", expected_volume)

    def test_GIVEN_calc_mode_is_volume_WHEN_setting_time_THEN_set_is_ignored(self):
        expected_time = self.ca.get_pv_value("TIME:RUN:SP")
        expected_volume = self.ca.get_pv_value("TIME:VOL:SP")
        self.ca.set_pv_value("TIME:CALC:SP", "Volume")

        self.ca.set_pv_value("TIME:RUN:SP", expected_time * 10)

        self.ca.assert_that_pv_is("TIME:RUN:SP", expected_time)
        self.ca.assert_that_pv_is("TIME:VOL:SP", expected_volume)

    @skip_if_recsim("Lewis device logic not supported in RECSIM")
    def test_GIVEN_input_incorrect_WHEN_set_flowrate_THEN_trouble_message_returned(self):
        self._lewis.backdoor_set_on_device("input_correct", False)
        self.ca.set_pv_value("FLOWRATE:SP", 0.010)

        self.ca.assert_that_pv_is("ERROR:STR", "[Error:stack underflow]")
