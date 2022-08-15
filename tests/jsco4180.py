import unittest
from time import sleep

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, unstable_test

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

TEST_MODES = [TestModes.DEVSIM]

ERROR_STATE_HARDWARE_FAULT = 4
ERROR_STATE_NO_ERROR = 2

required_pvs = ["COMP:A:SP", "COMP:B:SP", "COMP:C:SP", "START:SP", "STATUS", "FLOWRATE:SP", "TIME:RUN:SP",
                "PRESSURE:MIN:SP", "PRESSURE:MAX:SP", "ERROR:SP", "ERROR:STR", "PUMP_FOR_TIME:SP"]


class Jsco4180Tests(unittest.TestCase):
    """
    Tests for the Jsco4180 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30, default_wait_time=0.0)
        for pv in required_pvs:
            self.ca.assert_that_pv_exists(pv, timeout=30)
        self._lewis.backdoor_run_function_on_device("reset")

    def test_GIVEN_wrong_component_on_device_WHEN_running_THEN_retry_run_and_updates_component(self):
        expected_value_A = 30
        expected_value_B = 15
        expected_value_C = 55

        self.ca.set_pv_value("COMP:A:SP", expected_value_A)
        self.ca.set_pv_value("COMP:B:SP", expected_value_B)
        self.ca.set_pv_value("COMP:C:SP", expected_value_C)

        self.ca.set_pv_value("START:SP", 1)

        sleep(10)
        # Setting an incorrect component on the device will result in the state machine attempting
        # to rerun the pump and reset components.
        self._lewis.backdoor_set_on_device("component_A", 25)
        self._lewis.backdoor_set_on_device("component_B", 10)
        self._lewis.backdoor_set_on_device("component_C", 14)

        self.ca.assert_that_pv_is("COMP:A", expected_value_A, timeout=30)
        self.ca.assert_that_pv_is("COMP:B", expected_value_B, timeout=30)
        self.ca.assert_that_pv_is("COMP:C", expected_value_C, timeout=30)

    # there was a previous problem where if setpoint and readback differed a sleep and resend was started,
    # but the old state machine did not look to see if a new sp was issued while it was asleep and so then
    # resent the old out of date SP
    @unstable_test(max_retries=2, wait_between_runs=60)
    def test_GIVEN_wrong_component_on_device_WHEN_send_new_sp_THEN_state_machine_aborts_resend(self):
        value = 50
        self.ca.set_pv_value("COMP:A:SP", value)
        self.ca.set_pv_value("COMP:B:SP", value)
        self.ca.set_pv_value("START:SP", 1)
        self.ca.assert_that_pv_is("STATUS", "Pumping", timeout=5)
        self.ca.assert_that_pv_is("COMP:A", value, timeout=30)
        self.ca.assert_that_pv_is("COMP:B", value, timeout=30)

        # Setting an incorrect component on the device will result in the state machine attempting
        # to rerun the pump and reset components after a delay
        initial_delay = self.ca.get_pv_value("ERROR:DELAY")  # delay before state machine reset
        delay = 30  # Increase delay to avoid race conditions
        self.ca.set_pv_value("ERROR:DELAY", delay)
        try:
            with self.ca.assert_pv_not_processed("RESET:SP"):
                self._lewis.backdoor_set_on_device("component_A", value - 5)
                self.ca.assert_that_pv_is("COMP:A", value - 5, timeout=5)
                sleep(delay / 2.0)

                # however if we change setpoint, the loop should start again
                self._lewis.backdoor_set_on_device("component_A", value - 5)
                self.ca.set_pv_value("COMP:A:SP", value - 10)
                self.ca.set_pv_value("COMP:B:SP", value + 10)
                # reset should not have happened yet
                self.ca.assert_that_pv_is("COMP:A", value - 5, timeout=delay / 2.0)
                self.ca.assert_that_pv_value_is_unchanged("COMP:A", wait=delay / 2.0)

            # Reset should now happen within a further timeout/2 seconds (but give it longer to avoid races)
            with self.ca.assert_pv_processed("RESET:SP"):
                self.ca.assert_that_pv_is("COMP:A", value - 10, timeout=delay * 2)
        finally:
            # Put error delay back to it's initial value
            self.ca.set_pv_value("ERROR:DELAY", initial_delay)

    def test_GIVEN_wrong_component_on_device_WHEN_running_continuous_THEN_retry_run_and_updates_component_in_correct_mode(
            self):
        self.ca.set_pv_value("COMP:C:SP", 0)

        value = 50
        expected_value = "Pumping"
        self.ca.set_pv_value("COMP:A:SP", value)
        self.ca.set_pv_value("COMP:B:SP", value)

        self.ca.set_pv_value("START:SP", 1)

        # Give the device some time running in a good state
        sleep(10)
        # Sabotage! - Setting an incorrect component on the device will result in the state machine attempting
        # to rerun the pump and reset components.
        self._lewis.backdoor_set_on_device("component_A", 33)

        self.ca.assert_that_pv_is("STATUS", expected_value, timeout=30)

    def test_GIVEN_wrong_component_on_device_WHEN_running_timed_THEN_retry_run_and_updates_component_in_correct_mode(
            self):
        value = 50
        expected_value = "Pumping"
        self.ca.set_pv_value("COMP:A:SP", value)
        self.ca.set_pv_value("COMP:B:SP", value)
        self.ca.set_pv_value("TIME:RUN:SP", 100)
        self.ca.set_pv_value("PUMP_FOR_TIME:SP", 1)

        # Give the device some time running in a good state
        sleep(10)
        # Sabotage! - Setting an incorrect component on the device will result in the state machine attempting
        # to rerun the pump and reset components.
        self._lewis.backdoor_set_on_device("component_A", 33)

        self.ca.assert_that_pv_is("STATUS", expected_value, timeout=30)

    def test_GIVEN_an_ioc_WHEN_set_flowrate_THEN_flowrate_setpoint_is_correct(self):

        error_delay = float(self.ca.get_pv_value("ERROR:DELAY"))
        sleep(2 * error_delay)  # To make sure we're not in the middle of the error-checking state machine

        expected_value = 1.000
        self.ca.set_pv_value("FLOWRATE:SP", expected_value)

        self.ca.assert_that_pv_is("FLOWRATE:SP:RBV", expected_value)

        self.ca.set_pv_value("TIME:RUN:SP", 100)
        self.ca.set_pv_value("START:SP", "Start")

        self.ca.assert_that_pv_is("FLOWRATE", expected_value)

    def test_GIVEN_an_ioc_WHEN_set_flowrate_and_pump_volume_THEN_ioc_uses_rbv_for_calculation_of_remaining_time(self):
        expected_sp_value = 1.000
        expected_rbv_value = 2.000
        pump_for_volume = 2
        expected_time_value = (pump_for_volume / expected_rbv_value) * 60

        error_delay = float(self.ca.get_pv_value("ERROR:DELAY"))
        sleep(2 * error_delay)  # To make sure we're not in the middle of the error-checking state machine

        # 1. set invalid flowrate setpoint (FLOWRATE:SP)
        self.ca.set_pv_value("FLOWRATE:SP", expected_sp_value)
        self.ca.assert_that_pv_is("FLOWRATE:SP:RBV", expected_sp_value)

        # 2. set valid hardware flowrate (FLOWRATE:SP:RBV) via backdoor command
        self._lewis.backdoor_set_on_device("flowrate_rbv", expected_rbv_value)
        self.ca.assert_that_pv_is("FLOWRATE:SP:RBV", expected_rbv_value)

        # 3. set volume setpoint and start pump
        self.ca.set_pv_value("TIME:VOL:SP", pump_for_volume)
        self.ca.set_pv_value("START:SP", "Start")

        # 4. check calculated time is based on flowrate setpoint readback (:SP:RBV rather than :SP)
        self.ca.assert_that_pv_is("TIME:VOL:CALCRUN", expected_time_value)

    def test_GIVEN_an_ioc_WHEN_set_flowrate_and_pump_time_THEN_ioc_uses_rbv_for_calculation_of_remaining_volume(self):
        expected_sp_value = 1.000
        expected_rbv_value = 2.000
        pump_for_time = 120
        expected_volume_value = (pump_for_time * expected_rbv_value) / 60

        error_delay = float(self.ca.get_pv_value("ERROR:DELAY"))
        sleep(2 * error_delay)  # To make sure we're not in the middle of the error-checking state machine

        # 1. set invalid flowrate setpoint (FLOWRATE:SP)
        self.ca.set_pv_value("FLOWRATE:SP", expected_sp_value)
        self.ca.assert_that_pv_is("FLOWRATE:SP:RBV", expected_sp_value)

        # 2. set valid hardware flowrate (FLOWRATE:SP:RBV) via backdoor command
        self._lewis.backdoor_set_on_device("flowrate_rbv", expected_rbv_value)
        self.ca.assert_that_pv_is("FLOWRATE:SP:RBV", expected_rbv_value)

        # 3. set time setpoint and start pump
        self.ca.set_pv_value("TIME:RUN:SP", pump_for_time)
        self.ca.set_pv_value("START:SP", "Start")

        # 4. check calculated volume is based on flowrate setpoint readback (:SP:RBV rather than :SP)
        self.ca.assert_that_pv_is("TIME:RUN:CALCVOL", expected_volume_value)

    # test to check that the IOC updates the flowrate RBV quickly enough
    # for the remaining volume calculation to be valid.  simulates operation of a script.
    def test_GIVEN_an_ioc_WHEN_set_flowrate_and_immediately_set_pump_to_start_THEN_ioc_updates_rbv_for_calculation_of_remaining_volume(
            self):
        expected_sp_value = 2.000
        script_sp_value = 3.000
        pump_for_time = 120

        # 1. initialize flowrate
        self.ca.set_pv_value("FLOWRATE:SP", expected_sp_value)
        self.ca.assert_that_pv_is("FLOWRATE:SP:RBV", expected_sp_value, timeout=5)

        # 2. set new flowrate and immediately set pump to run, to simulate script
        self.ca.set_pv_value("FLOWRATE:SP", script_sp_value)
        self.ca.set_pv_value("TIME:RUN:SP", pump_for_time)
        self.ca.set_pv_value("START:SP", "Start")

        # 3. calculate remaining volume
        expected_volume_value = (pump_for_time * self.ca.get_pv_value("FLOWRATE:SP:RBV")) / 60

        # 4. check ioc calculation is as expected
        self.ca.assert_that_pv_is("TIME:RUN:CALCVOL", expected_volume_value)

    def test_GIVEN_an_ioc_WHEN_set_maximum_pressure_limit_THEN_maximum_pressure_limit_is_correct(self):
        expected_value = 200
        self.ca.assert_setting_setpoint_sets_readback(expected_value, "PRESSURE:MAX")

    def test_GIVEN_an_ioc_WHEN_set_minimum_pressure_limit_THEN_minimum_pressure_limit_is_correct(self):
        expected_value = 100
        self.ca.set_pv_value("PRESSURE:MIN:SP", expected_value)
        self.ca.assert_setting_setpoint_sets_readback(expected_value, "PRESSURE:MIN")

    def test_GIVEN_an_ioc_WHEN_continuous_pump_set_THEN_pump_on(self):
        self.ca.set_pv_value("START:SP", 1)

        self.ca.assert_that_pv_is("STATUS", "Pumping")

    def test_GIVEN_an_ioc_WHEN_timed_pump_set_THEN_timed_pump_on(self):
        # Set a run time for a timed run
        self.ca.set_pv_value("TIME:RUN:SP", 10000)
        self.ca.set_pv_value("PUMP_FOR_TIME:SP", 1)

        self.ca.assert_that_pv_is("STATUS", "Pumping")

    def test_GIVEN_an_ioc_WHEN_get_current_pressure_THEN_current_pressure_returned(self):
        expected_value = 300
        self._lewis.backdoor_set_on_device("pressure", expected_value)

        self.ca.assert_that_pv_is("PRESSURE", expected_value)

    @parameterized.expand([
        ("component_{}".format(suffix), suffix) for suffix in ["A", "B", "C", "D"]
    ])
    def test_GIVEN_an_ioc_WHEN_get_component_THEN_correct_component_returned(self, component, suffix):
        expected_value = 10.0
        self._lewis.backdoor_set_on_device(component, expected_value)

        self.ca.assert_that_pv_is("COMP:{}".format(suffix), expected_value)

    @parameterized.expand([
        ("COMP:{}".format(suffix), suffix) for suffix in ["A", "B", "C"]
    ])
    def test_GIVEN_an_ioc_WHEN_set_component_THEN_correct_component_set(self, component, suffix):
        expected_value = 100.0
        self.ca.set_pv_value("COMP:{}:SP".format(suffix), expected_value)
        if component == "COMP:A":
            self.ca.set_pv_value("COMP:B:SP", 0)
            self.ca.set_pv_value("COMP:C:SP", 0)
        elif component == "COMP:B":
            self.ca.set_pv_value("COMP:A:SP", 0)
            self.ca.set_pv_value("COMP:C:SP", 0)
        elif component == "COMP:C":
            self.ca.set_pv_value("COMP:A:SP", 0)
            self.ca.set_pv_value("COMP:B:SP", 0)
        self.ca.set_pv_value("PUMP_FOR_TIME:SP", "Start")

        self.ca.assert_that_pv_is(component, expected_value)

    def test_GIVEN_ioc_initial_state_WHEN_get_error_THEN_error_returned(self):
        expected_value = "No error"

        self.ca.assert_that_pv_is("ERROR", expected_value)

    def test_GIVEN_ioc_in_hardware_error_state_WHEN_get_error_THEN_hardware_error_returned(self):
        expected_value = "Hardware error"
        self._lewis.backdoor_set_on_device("error", ERROR_STATE_HARDWARE_FAULT)

        self.ca.assert_that_pv_is("ERROR", expected_value)

    def test_GIVEN_ioc_in_error_state_WHEN_reset_error_THEN_error_reset(self):
        expected_value = "No error"
        self._lewis.backdoor_set_on_device("error", ERROR_STATE_NO_ERROR)
        self.ca.set_pv_value("ERROR:SP", "Reset")

        self.ca.assert_that_pv_is("ERROR", expected_value)

    def test_GIVEN_ioc_in_error_state_WHEN_reset_error_THEN_error_reset(self):
        expected_value = "No error"
        self._lewis.backdoor_set_on_device("error", ERROR_STATE_HARDWARE_FAULT)

        self.ca.assert_that_pv_is("ERROR", expected_value)

    def test_GIVEN_device_not_connected_WHEN_get_error_THEN_alarm(self):
        self.ca.assert_that_pv_alarm_is('ERROR:SP', ChannelAccess.Alarms.NONE, timeout=30)

        with self._lewis.backdoor_simulate_disconnected_device():
            self.ca.assert_that_pv_alarm_is('ERROR:SP', ChannelAccess.Alarms.INVALID, timeout=30)
            
        # Assert alarms clear on reconnection
        self.ca.assert_that_pv_alarm_is('ERROR:SP', ChannelAccess.Alarms.NONE, timeout=30)

    def test_GIVEN_timed_pump_WHEN_get_program_runtime_THEN_program_runtime_increments(self):
        self.ca.set_pv_value("TIME:RUN:SP", 10000)
        self.ca.set_pv_value("PUMP_FOR_TIME:SP", 1)

        self.ca.assert_that_pv_value_is_increasing("TIME", wait=2)

    def test_GIVEN_timed_pump_WHEN_set_constant_pump_THEN_state_updated_to_constant_pump(self):
        # Set a run time for a timed run
        self.ca.set_pv_value("TIME:RUN:SP", 10000)
        self.ca.process_pv("PUMP_FOR_TIME:SP")
        expected_value = "Pumping"
        self.ca.assert_that_pv_is("STATUS", expected_value)

        self.ca.process_pv("START:SP")
        expected_value = "Pumping"
        self.ca.assert_that_pv_is("STATUS", expected_value)

    def test_GIVEN_constant_pump_WHEN_set_timed_pump_THEN_state_updated_to_timed_pump(self):
        expected_value = "Pumping"

        self.ca.process_pv("START:SP")
        self.ca.assert_that_pv_is("STATUS", expected_value)

        # Set a run time for a timed run
        self.ca.set_pv_value("TIME:RUN:SP", 10000)
        self.ca.process_pv("PUMP_FOR_TIME:SP")
        self.ca.assert_that_pv_is("STATUS", expected_value)

    def test_GIVEN_input_incorrect_WHEN_set_flowrate_THEN_trouble_message_returned(self):
        self._lewis.backdoor_set_on_device("input_correct", False)
        self.ca.set_pv_value("FLOWRATE:SP", 0.010)

        self.ca.assert_that_pv_is("ERROR:STR", "[Error:stack underflow]")

    def test_GIVEN_command_seq_that_would_crash_pump_WHEN_command_seq_called_THEN_pump_crashes(self):
        self.ca.set_pv_value("_TEST_CRASH.PROC", 1)

        self.ca.assert_that_pv_alarm_is("COMP:A", ChannelAccess.Alarms.INVALID, timeout=30)

    def test_GIVEN_pump_running_WHEN_set_file_number_command_called_THEN_program_is_busy_error(self):
        expected_value = "[Program is Busy]"
        self.ca.set_pv_value("START:SP", 1)
        self.ca.set_pv_value("FILE:SP", 0)

        self.ca.assert_that_pv_is("ERROR:STR", expected_value)

    @parameterized.expand([("low_set_time", 100, 1, 1),
                           ("high_set_time", 1000, 10, 1),
                           ("non_standard_set_time", 456, 5, 1)])
    @unstable_test(max_retries=5)
    def test_GIVEN_pump_for_volume_WHEN_pumping_THEN_device_is_pumping_set_volume(self, _, time, volume, flowrate):
        # Set a target pump time a target pump volume. When we start a pump set volume run, then the remaining
        # time should be related to the target volume, and not the target time (that would be used for a pump for time).
        set_time = time
        set_volume = volume
        set_flowrate = flowrate
        expected_time = set_volume * set_flowrate * 60  # flow rate units = mL/min, so convert to seconds

        self.ca.set_pv_value("TIME:RUN:SP", set_time)
        self.ca.set_pv_value("TIME:VOL:SP", set_volume)
        self.ca.set_pv_value("FLOWRATE:SP", set_flowrate)

        self.ca.process_pv("PUMP_SET_VOLUME:SP")

        self.ca.assert_that_pv_is_within_range("TIME:REMAINING", min_value=expected_time - 20,
                                               max_value=expected_time + 20)

