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

    def test_GIVEN_an_ioc_WHEN_set_flowrate_THEN_flowrate_setpoint_is_correct(self):
        expected_value = 1.000
        self.ca.set_pv_value("FLOWRATE:SP", expected_value)

        self.ca.assert_that_pv_is("FLOWRATE:SP:RBV", expected_value, timeout=1)

    def test_GIVEN_an_ioc_WHEN_set_maximum_pressure_limit_THEN_maximum_pressure_limit_is_correct(self):
        expected_value = 200
        self.ca.set_pv_value("PRESSURE:MAX:SP", expected_value)

        self.ca.assert_that_pv_is("PRESSURE:MAX", expected_value, timeout=1)

    def test_GIVEN_an_ioc_WHEN_set_minimum_pressure_limit_THEN_minimum_pressure_limit_is_correct(self):
        expected_value = 100
        self.ca.set_pv_value("PRESSURE:MIN:SP", expected_value)

        self.ca.assert_that_pv_is("PRESSURE:MIN", expected_value, timeout=1)

    def test_GIVEN_and_ioc_WHEN_set_pump_off_timer_THEN_pump_off_timer_set(self):
        expected_value = 12.4
        self.ca.set_pv_value("_PUMP:TIMER:OFF", expected_value)

        self.ca.assert_that_pv_is("_PUMP:TIMER:OFF", expected_value)

    def test_GIVEN_and_ioc_WHEN_set_pump_on_timer_THEN_pump_on_timer_set(self):
        expected_value = 50.4
        self.ca.set_pv_value("_PUMP:TIMER:ON", expected_value)

        self.ca.assert_that_pv_is("_PUMP:TIMER:ON", expected_value)

    def test_GIVEN_an_ioc_WHEN_set_valve_position_THEN_valve_positon_updated(self):
        expected_value = 4
        self.ca.set_pv_value("VALVE:POS:SP", expected_value)

        self.ca.assert_that_pv_is("VALVE:POS", expected_value, timeout=1)

    def test_GIVEN_an_ioc_WHEN_set_file_number_THEN_file_number_set(self):
        expected_value = "File 3"
        self.ca.set_pv_value("FILE:NUM:SP", expected_value)

        self.ca.assert_that_pv_is("FILE:NUM", expected_value)

    def test_GIVEN_an_ioc_WHEN_open_file_THEN_file_opened(self):
        self.ca.set_pv_value("FILE:OPEN:SP", "Open")

        self.ca.assert_that_pv_is("FILE:OPEN", "Open")

    def test_GIVEN_an_ioc_WHEN_close_file_THEN_file_closed(self):
        self.ca.set_pv_value("FILE:CLOSE:SP", "Close")

        self.ca.assert_that_pv_is("FILE:CLOSE", "Close")

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

        self.ca.assert_that_pv_is("PRESSURE", expected_value, timeout=1)

    @parameterized.expand([
        ("component_{}".format(suffix), suffix) for suffix in ["A", "B", "C", "D"]
    ])
    @skip_if_recsim("Reliant on setUP lewis backdoor call")
    def test_GIVEN_an_ioc_WHEN_get_component_THEN_correct_component_returned(self, component, suffix):
        expected_value = 10.0
        self._lewis.backdoor_set_on_device(component, expected_value)

        self.ca.assert_that_pv_is("COMP:{}".format(suffix), expected_value, timeout=4)

    @parameterized.expand([
        ("COMP:{}".format(suffix), suffix) for suffix in ["A", "B", "C"]
    ])
    @skip_if_recsim("Reliant on setUP lewis backdoor call")
    def test_GIVEN_an_ioc_WHEN_set_component_THEN_correct_component_set(self, component, suffix):
        expected_value = 100.0
        self.ca.set_pv_value("COMP:{}:SP".format(suffix), expected_value)
        # Call the hidden function rather than the normal full sequence (START:SP) as we are testing this
        # specific set composition record
        self.ca.set_pv_value("_COMP:SP", "Set")

        self.ca.assert_that_pv_is(component, expected_value, timeout=4)

    def test_GIVEN_ioc_initial_state_WHEN_get_error_THEN_error_returned(self):
        expected_value = "No error"

        self.ca.assert_that_pv_is("ERROR", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_ioc_in_error_state_WHEN_get_error_THEN_error_returned(self):
        expected_value = "Hardware error"
        self._lewis.backdoor_set_on_device("error", 4)

        self.ca.assert_that_pv_is("ERROR", expected_value, timeout=2)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_ioc_in_error_state_WHEN_reset_error_THEN_error_reset(self):
        expected_value = "No error"
        self._lewis.backdoor_set_on_device("error", 2)
        self.ca.set_pv_value("ERROR:SP", "Reset")

        self.ca.assert_that_pv_is("ERROR", expected_value, timeout=1)

    def test_GIVEN_an_ioc_WHEN_set_composition_time_setpoint_THEN_time_set(self):
        expected_value = 23.5
        self.ca.set_pv_value("COMP:TIME:SP", expected_value)

        self.ca.assert_that_pv_is("COMP:TIME", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_an_input_error_WHEN_open_file_THEN_file_error_str_returned(self):
        self._lewis.backdoor_set_on_device("input_correct", False)
        expected_value = "[Error:file open error]"
        self.ca.set_pv_value("FILE:OPEN:SP", "Open")

        self.ca.assert_that_pv_is("ERROR:STR", expected_value)

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
        self.ca.assert_that_pv_is("TIME:MODE", expected_value, timeout=3)

        self.ca.set_pv_value("START:SP", 1)
        expected_value = "CONTINUOUS"
        self.ca.assert_that_pv_is("TIME:MODE", expected_value, timeout=3)

    def test_GIVEN_constant_pump_WHEN_set_timed_pump_THEN_state_updated_to_timed_pump(self):
        self.ca.set_pv_value("START:SP", 1)
        expected_value = "CONTINUOUS"
        self.ca.assert_that_pv_is("TIME:MODE", expected_value, timeout=3)

        # Set a run time for a timed run
        self.ca.set_pv_value("TIME:RUN:SP", 10000)
        self.ca.set_pv_value("TIMED:SP", 1)
        expected_value = "TIMED"
        self.ca.assert_that_pv_is("TIME:MODE", expected_value, timeout=3)

    def test_GIVEN_calc_mode_is_time_WHEN_setting_time_THEN_time_and_volume_are_correctly_set(self):
        expected_time = 600
        expected_volume = 0.1
        self.ca.set_pv_value("TIME:CALC:SP", "Time")

        self.ca.set_pv_value("TIME:RUN:SP", expected_time)

        self.ca.assert_that_pv_is("TIME:RUN:SP", expected_time, timeout=3)
        self.ca.assert_that_pv_is("TIME:VOL:SP", expected_volume, timeout=3)

    def test_GIVEN_calc_mode_is_time_WHEN_setting_volume_THEN_set_is_ignored(self):
        expected_time = self.ca.get_pv_value("TIME:RUN:SP")
        expected_volume = self.ca.get_pv_value("TIME:VOL:SP")
        self.ca.set_pv_value("TIME:CALC:SP", "Time")

        self.ca.set_pv_value("TIME:VOL:SP", expected_volume * 10)

        self.ca.assert_that_pv_is("TIME:RUN:SP", expected_time, timeout=3)
        self.ca.assert_that_pv_is("TIME:VOL:SP", expected_volume, timeout=3)

    def test_GIVEN_calc_mode_is_volume_WHEN_setting_volume_THEN_time_and_volume_are_correctly_set(self):
        expected_time = 600
        expected_volume = 0.1
        self.ca.set_pv_value("TIME:CALC:SP", "Volume")

        self.ca.set_pv_value("TIME:VOL:SP", expected_volume)

        self.ca.assert_that_pv_is("TIME:RUN:SP", expected_time, timeout=3)
        self.ca.assert_that_pv_is("TIME:VOL:SP", expected_volume, timeout=3)

    def test_GIVEN_calc_mode_is_volume_WHEN_setting_time_THEN_set_is_ignored(self):
        expected_time = self.ca.get_pv_value("TIME:RUN:SP")
        expected_volume = self.ca.get_pv_value("TIME:VOL:SP")
        self.ca.set_pv_value("TIME:CALC:SP", "Volume")

        self.ca.set_pv_value("TIME:RUN:SP", expected_time * 10)

        self.ca.assert_that_pv_is("TIME:RUN:SP", expected_time, timeout=3)
        self.ca.assert_that_pv_is("TIME:VOL:SP", expected_volume, timeout=3)

