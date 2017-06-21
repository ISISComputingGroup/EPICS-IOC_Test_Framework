import unittest
from unittest import skipIf
from time import sleep

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

import math

WAVEFORM_STOPPED = "0"
WAVEFORM_RUNNING = "1"
WAVEFORM_ABORTED = "4"
NUMBER_OF_CHANNELS = 3


def prefixed(val):
    return "{0}{1}".format("INSTRON_01:", val)


def wave_prefixed(val):
    return prefixed("{0}{1}".format("WAVE:", val))


class Instron_stress_rigTests(unittest.TestCase):
    """
    Tests for the Instron IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("instron_stress_rig")

        self.ca = ChannelAccess(15)
        self.ca.wait_for(prefixed("CHANNEL"), timeout=30)

    #def test_WHEN_the_rig_is_initialized_THEN_the_status_is_ok(self):
    #    self.ca.assert_that_pv_is(prefixed("STAT:DISP"), "System OK")
    #
    #def test_WHEN_the_rig_is_initialized_THEN_it_is_not_going(self):
    #    self.ca.assert_that_pv_is(prefixed("GOING"), "NO")
    #
    #def test_WHEN_the_rig_is_initialized_THEN_it_is_not_panic_stopping(self):
    #    self.ca.assert_that_pv_is(prefixed("PANIC:SP"), "READY")
    #
    #def test_WHEN_the_rig_is_initialized_THEN_it_is_not_stopping(self):
    #    self.ca.assert_that_pv_is(prefixed("STOP:SP"), "READY")
    #
    #def test_that_the_rig_is_not_normally_in_control_mode(self):
    #    self.ca.assert_that_pv_is(prefixed("STOP:SP"), "READY")
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_going_and_then_stopping_THEN_going_pv_reflects_the_expected_state(self):
    #    self.ca.assert_that_pv_is(prefixed("GOING"), "NO")
    #    self.ca.set_pv_value(prefixed("MOVE:GO:SP"), 1)
    #    self.ca.assert_that_pv_is(prefixed("GOING"), "YES")
    #    self.ca.set_pv_value(prefixed("STOP:SP"), 1)
    #    self.ca.assert_that_pv_is(prefixed("GOING"), "NO")
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_going_and_then_panic_stopping_THEN_going_pv_reflects_the_expected_state(self):
    #    self.ca.assert_that_pv_is(prefixed("GOING"), "NO")
    #    self.ca.set_pv_value(prefixed("MOVE:GO:SP"), 1)
    #    self.ca.assert_that_pv_is(prefixed("GOING"), "YES")
    #    self.ca.set_pv_value(prefixed("PANIC:SP"), 1)
    #    self.ca.assert_that_pv_is(prefixed("GOING"), "NO")
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_arbitrary_command_Q22_is_sent_THEN_the_response_is_a_status_code(self):
    #    self.ca.set_pv_value(prefixed("ARBITRARY:SP"), "Q22")
    #    # Assert that the response to Q22 is a status code
    #    self.ca.assert_that_pv_is_an_integer_between(prefixed("ARBITRARY"), min=0, max=65535)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_arbitrary_command_Q300_is_sent_THEN_the_response_is_a_number_between_1_and_3(self):
    #    self.ca.set_pv_value(prefixed("ARBITRARY:SP"), "Q300")
    #    # Assert that the response to Q300 is between 1 and 3
    #    self.ca.assert_that_pv_is_an_integer_between(prefixed("ARBITRARY"), min=1, max=3)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_arbitrary_command_C1_is_sent_THEN_Q1_gives_back_the_value_that_was_just_set(self):
    #
    #    def _set_and_check(value):
    #        self.ca.set_pv_value(prefixed("ARBITRARY:SP"), "C1," + value)
    #        self.ca.assert_that_pv_is(prefixed("ARBITRARY:SP"), "C1," + value)
    #        self.ca.set_pv_value(prefixed("ARBITRARY:SP"), "Q1")
    #        self.ca.assert_that_pv_is(prefixed("ARBITRARY"), value)
    #
    #    for v in ["0"), "1"), "0"]:
    #        _set_and_check(v)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_the_movement_type_on_rig_is_hold_THEN_it_gets_stopped(self):
    #
    #    self.ca.set_pv_value(prefixed("MOVE:SP"), 1)
    #    self.ca.assert_that_pv_is_one_of(prefixed("MOVE"), ["RAMP_RUNNING"), "RAND_RUNNING"])
    #
    #    self.ca.set_pv_value(prefixed("MOVE:SP"), 2)
    #    self.ca.assert_that_pv_is(prefixed("MOVE"), "STOPPED")
    #
    #def test_WHEN_control_channel_is_requested_THEN_an_allowed_value_is_returned(self):
    #    self.ca.assert_that_pv_is_one_of(prefixed("CHANNEL"), ["Stress"), "Strain"), "Position"])
    #
    #def test_WHEN_control_channel_setpoint_is_requested_THEN_it_is_one_of_the_allowed_values(self):
    #    self.ca.assert_that_pv_is_one_of(prefixed("CHANNEL:SP"), ["Stress"), "Strain"), "Position"])
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_the_control_channel_is_set_THEN_the_readback_contains_the_value_that_was_just_set(self):
    #
    #    def _set_and_check(set_value, return_value):
    #        self.ca.set_pv_value(prefixed("CHANNEL:SP"), set_value)
    #        self.ca.assert_that_pv_is(prefixed("CHANNEL"), return_value)
    #
    #    for set_val, return_val in [(0, "Position"), (1, "Stress"), (2, "Strain")]:
    #        _set_and_check(set_val, return_val)
    #
    #def test_WHEN_the_step_time_for_various_channels_is_set_as_an_integer_THEN_the_readback_contains_the_value_that_was_just_set(
    #        self):
    #
    #    def _set_and_check(chan, value):
    #        self.ca.set_pv_value(prefixed("" + chan + ":STEP:TIME:SP"), value)
    #        self.ca.assert_that_pv_is(prefixed("" + chan + ":STEP:TIME"), value)
    #
    #    for chan, val in [("POS"), 123), ("STRESS"), 456), ("STRAIN"), 789)]:
    #        _set_and_check(chan, val)
    #
    #def test_WHEN_the_step_time_for_various_channels_is_set_as_a_float_THEN_the_readback_contains_the_value_that_was_just_set(
    #        self):
    #
    #    def _set_and_check(chan, value):
    #        self.ca.set_pv_value(prefixed("" + chan + ":STEP:TIME:SP"), value)
    #        self.ca.assert_that_pv_is(prefixed("" + chan + ":STEP:TIME"), value)
    #
    #    for chan, val in [("POS"), 111.111), ("STRESS"), 222.222), ("STRAIN"), 333.333)]:
    #        _set_and_check(chan, val)
    #
    #def test_WHEN_the_ramp_waveform_for_a_channel_is_set_THEN_the_readback_contains_the_value_that_was_just_set(self):
    #
    #    def _set_and_check(chan, set_value, return_value):
    #        self.ca.set_pv_value(prefixed("" + chan + ":ABS:SP"), set_value)
    #        self.ca.assert_that_pv_is(prefixed("" + chan + ":ABS"), return_value)
    #
    #    for chan in ["POS"), "STRESS"), "STRAIN"]:
    #        for set_value, return_value in [(0, "Ramp"),
    #                                        (1, "Dual ramp"),
    #                                        (2, "Trapezium"),
    #                                        (3, "Absolute ramp"),
    #                                        (4, "Absolute hold ramp"),
    #                                        (5, "Absolute rate ramp"),]:
    #
    #            _set_and_check(chan, set_value, return_value)
    #
    #def test_WHEN_the_ramp_amplitude_for_a_channel_is_set_as_an_integer_THEN_the_readback_contains_the_value_that_was_just_set(self):
    #    def _set_and_check(chan, value):
    #        self.ca.set_pv_value(prefixed("" + chan + ":RAW:SP"), value)
    #        self.ca.assert_that_pv_is(prefixed("" + chan + ":RAW:SP:RBV"), value)
    #
    #    for chan in ["POS"), "STRESS"), "STRAIN"]:
    #        for i in [0,10,1000,1000000]:
    #            _set_and_check(chan, i)
    #
    #def test_WHEN_the_ramp_amplitude_for_a_channel_is_set_as_a_float_THEN_the_readback_contains_the_value_that_was_just_set(self):
    #    def _set_and_check(chan, value):
    #        self.ca.set_pv_value(prefixed("" + chan + ":RAW:SP"), value)
    #        self.ca.assert_that_pv_is(prefixed("" + chan + ":RAW:SP:RBV"), value)
    #
    #    for chan in ["POS"), "STRESS"), "STRAIN"]:
    #        for i in [1.0, 5.5, 1.000001, 9.999999, 10000.1]:
    #            _set_and_check(chan, i)
    #
    #def test_WHEN_channel_tolerance_is_set_THEN_it_changes(self):
    #    def _set_and_check(chan, value):
    #        self.ca.set_pv_value(prefixed("" + chan + ":TOLERANCE"), value)
    #        self.ca.assert_that_pv_is(prefixed("" + chan + ":TOLERANCE"), value)
    #
    #    for chan in ["POS"), "STRESS"), "STRAIN"]:
    #        for i in [0.1, 1.0, 2.5]:
    #            _set_and_check(chan, i)
    #
    #def test_GIVEN_a_big_tolerance_WHEN_the_setpoint_is_set_THEN_the_setpoint_has_no_alarms(self):
    #    def _set_and_check(chan, value):
    #        self.ca.set_pv_value(prefixed("" + chan + ":SP"), value)
    #        self.ca.set_pv_value(prefixed("" + chan + ":TOLERANCE"), 9999)
    #        self.ca.assert_pv_alarm_is(prefixed("" + chan + ":SP:RBV"), ChannelAccess.ALARM_NONE)
    #
    #    for chan in ["POS"), "STRESS"), "STRAIN"]:
    #        for i in [0.123, 567]:
    #            _set_and_check(chan, i)
    #
    #def test_GIVEN_a_tolerance_of_minus_one_WHEN_the_setpoint_is_set_THEN_the_setpoint_has_alarms(
    #        self):
    #    def _set_and_check(chan, value):
    #        self.ca.set_pv_value(prefixed("" + chan + ":SP"), value)
    #        self.ca.set_pv_value(prefixed("" + chan + ":TOLERANCE"), -1)
    #        self.ca.assert_pv_alarm_is(prefixed("" + chan + ":SP:RBV"), ChannelAccess.ALARM_MINOR)
    #
    #    for chan in ["POS"), "STRESS"), "STRAIN"]:
    #        for i in [0.234, 789]:
    #            _set_and_check(chan, i)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_ioc_gets_a_raw_position_reading_from_the_device_THEN_it_is_converted_correctly(self):
    #
    #    for chan_scale in [0.1, 10.0]:
    #        self._lewis.backdoor_command(["device", "set_channel_param"), "1"), "scale"), str(chan_scale)])
    #        self.ca.assert_that_pv_is(prefixed("POS:SCALE"), chan_scale)
    #
    #        for raw_value in [0, 123]:
    #            self._lewis.backdoor_command(["device", "set_channel_param"), "1"), "value"), str(raw_value)])
    #            self.ca.assert_that_pv_is(prefixed("POS:RAW"), raw_value)
    #            self.ca.assert_that_pv_is(prefixed("POS"), raw_value * chan_scale * 1000)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_ioc_gets_a_raw_stress_reading_from_the_device_THEN_it_is_converted_correctly(self):
    #
    #    for chan_area in [0.1, 10.0]:
    #        self._lewis.backdoor_command(["device", "set_channel_param"), "2"), "area"), str(chan_area)])
    #        self.ca.assert_that_pv_is(prefixed("STRESS:AREA"), chan_area)
    #
    #        for chan_scale in [0.1, 10.0]:
    #            self._lewis.backdoor_command(["device", "set_channel_param"), "2"), "scale"), str(chan_scale)])
    #            self.ca.assert_that_pv_is(prefixed("STRESS:SCALE"), chan_scale)
    #
    #            for raw_value in [0, 123]:
    #                self._lewis.backdoor_command(["device", "set_channel_param"), "2"), "value"), str(raw_value)])
    #                self.ca.assert_that_pv_is(prefixed("STRESS:RAW"), raw_value)
    #                self.ca.assert_that_pv_is(prefixed("STRESS"), raw_value * chan_scale * (1.0/chan_area))
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_strain_length_updates_on_device_THEN_pv_updates(self):
    #    for value in [1,123]:
    #        self._lewis.backdoor_command(["device", "set_channel_param"), "3"), "length"), str(value)])
    #        self.ca.assert_that_pv_is(prefixed("STRAIN:LENGTH"), value)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_ioc_gets_a_raw_strain_reading_from_the_device_THEN_it_is_converted_correctly(self):
    #    for chan_scale in [0.1, 10.0]:
    #        self._lewis.backdoor_command(["device", "set_channel_param"), "3"), "scale"), str(chan_scale)])
    #
    #        for chan_length in [0.1, 10.0]:
    #            self._lewis.backdoor_command(["device", "set_channel_param"), "3"), "length"), str(chan_length)])
    #
    #            for raw_value in [0, 0.001]:
    #                self._lewis.backdoor_command(["device", "set_channel_param"), "3"), "value"), str(raw_value)])
    #
    #                self.ca.assert_that_pv_is(prefixed("STRAIN:SCALE"), chan_scale)
    #                self.ca.assert_that_pv_is(prefixed("STRAIN:LENGTH"), chan_length)
    #                self.ca.assert_that_pv_is(prefixed("STRAIN:RAW"), raw_value)
    #
    #                self.ca.assert_that_pv_is(prefixed("STRAIN"), (raw_value * chan_scale * 100000 * (1/chan_length)))
    #
    #def test_WHEN_the_area_setpoint_is_set_THEN_the_area_readback_updates(self):
    #    def _set_and_check(value):
    #        self.ca.set_pv_value(prefixed("STRESS:AREA:SP"), value)
    #        self.ca.assert_that_pv_is(prefixed("STRESS:AREA"), value)
    #        self.ca.assert_pv_alarm_is(prefixed("STRESS:AREA"), ChannelAccess.ALARM_NONE)
    #
    #    for val in [0.234, 789]:
    #        _set_and_check(val)
    #
    #def test_WHEN_the_area_setpoint_is_set_THEN_the_diameter_readback_updates(self):
    #    def _set_and_check(value):
    #        self.ca.set_pv_value(prefixed("STRESS:AREA:SP"), value)
    #        self.ca.assert_that_pv_is(prefixed("STRESS:DIAMETER"), (2*math.sqrt(value/math.pi)))
    #        self.ca.assert_pv_alarm_is(prefixed("STRESS:DIAMETER"), ChannelAccess.ALARM_NONE)
    #
    #    for val in [0.234, 789]:
    #        _set_and_check(val)
    #
    #def test_WHEN_the_diameter_setpoint_is_set_THEN_the_diameter_readback_updates(self):
    #    def _set_and_check(value):
    #        self.ca.set_pv_value(prefixed("STRESS:DIAMETER:SP"), value)
    #        self.ca.assert_that_pv_is_number(prefixed("STRESS:DIAMETER"), value, tolerance=0.0005)
    #        self.ca.assert_pv_alarm_is(prefixed("STRESS:DIAMETER"), ChannelAccess.ALARM_NONE)
    #
    #    for val in [0.234, 789]:
    #        _set_and_check(val)
    #
    #def test_WHEN_the_diameter_setpoint_is_set_THEN_the_area_readback_updates(self):
    #    def _set_and_check(value):
    #        self.ca.set_pv_value(prefixed("STRESS:DIAMETER:SP"), value)
    #        self.ca.assert_that_pv_is_number(prefixed("STRESS:AREA"), ((value/2.0)**2 * math.pi), tolerance=0.0005)
    #        self.ca.assert_pv_alarm_is(prefixed("STRESS:AREA"), ChannelAccess.ALARM_NONE)
    #
    #    for val in [0.234, 789]:
    #        _set_and_check(val)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_a_position_setpoint_is_set_THEN_it_is_converted_correctly(self):
    #    for scale in [2.34, 456.78]:
    #        self._lewis.backdoor_command(["device", "set_channel_param"), "1"), "scale"), str(scale)])
    #        self.ca.assert_that_pv_is(prefixed("POS:SCALE"), scale)
    #
    #        for val in [1.23, 123.45]:
    #            self.ca.set_pv_value(prefixed("POS:SP"), val)
    #            self.ca.assert_that_pv_is_number(prefixed("POS:RAW:SP"), val * (1.0/1000.0) * (1/scale), tolerance=0.0000000001)
    #            self.ca.assert_pv_alarm_is(prefixed("POS:RAW:SP"), ChannelAccess.ALARM_NONE)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_a_stress_setpoint_is_set_THEN_it_is_converted_correctly(self):
    #
    #    for area in [789, 543.21]:
    #        self._lewis.backdoor_command(["device", "set_channel_param"), "2"), "area"), str(area)])
    #        self.ca.assert_that_pv_is(prefixed("STRESS:AREA"), area)
    #
    #        for chan_scale in [2.34, 456.78]:
    #            self._lewis.backdoor_command(["device", "set_channel_param"), "2"), "scale"), str(chan_scale)])
    #            self.ca.assert_that_pv_is(prefixed("STRESS:SCALE"), chan_scale)
    #
    #            for val in [1.23, 123.45]:
    #                self.ca.set_pv_value(prefixed("STRESS:SP"), val)
    #                self.ca.assert_that_pv_is_number(prefixed("STRESS:RAW:SP"), val * (1 / chan_scale) * area,
    #                                                 tolerance=0.0000000001)
    #                self.ca.assert_pv_alarm_is(prefixed("STRESS:RAW:SP"), ChannelAccess.ALARM_NONE)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_a_strain_setpoint_is_set_THEN_it_is_converted_correctly(self):
    #
    #    for length in [789, 543.21]:
    #        self._lewis.backdoor_command(["device", "set_channel_param"), "3"), "length"), str(length)])
    #        self.ca.assert_that_pv_is(prefixed("STRAIN:LENGTH"), length)
    #
    #        for chan_scale in [2.34, 456.78]:
    #            self._lewis.backdoor_command(["device", "set_channel_param"), "3"), "scale"), str(chan_scale)])
    #            self.ca.assert_that_pv_is(prefixed("STRAIN:SCALE"), chan_scale)
    #
    #            for val in [1.23, 123.45]:
    #                self.ca.set_pv_value(prefixed("STRAIN:SP"), val)
    #                self.ca.assert_that_pv_is_number(prefixed("STRAIN:RAW:SP"), val * (1 / chan_scale) * length * (1.0/100000.0),
    #                                                 tolerance=0.0000000001)
    #                self.ca.assert_pv_alarm_is(prefixed("STRAIN:RAW:SP"), ChannelAccess.ALARM_NONE)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_the_channel_type_updates_on_the_device_THEN_the_pv_updates(self):
    #
    #    for chan_name, chan_num in [("POS"), 1), ("STRESS"), 2), ("STRAIN"), 3)]:
    #        for value_1, value_2, return_value_1, return_value_2 in [
    #                (0, 1, "Standard transducer"), "Unrecognized"),
    #                (1, 10, "User transducer"), "Ext. waveform generator")]:
    #
    #            self._lewis.backdoor_command(["device", "set_channel_param"), str(chan_num), "type_1"), str(value_1)])
    #            self._lewis.backdoor_command(["device", "set_channel_param"), str(chan_num), "type_2"), str(value_2)])
    #            self.ca.assert_that_pv_is(prefixed(""+chan_name+":TYPE:STANDARD"), return_value_1)
    #            self.ca.assert_that_pv_is(prefixed(""+chan_name+":TYPE"), return_value_2)

    # Waveform tests

    #def check_running_state(self, status, running, continuing):
    #    self.ca.assert_that_pv_is(wave_prefixed("STATUS"), status)
    #    self.ca.assert_that_pv_is(wave_prefixed("RUNNING"), "Running" if running else "Not running")
    #    self.ca.assert_that_pv_is(wave_prefixed("CONTINUING"), "Continuing" if continuing else "Not continuing")
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_GIVEN_the_waveform_generator_is_stopped_WHEN_it_is_started_THEN_it_is_running(self):
    #    self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_STOPPED])
    #    self.check_running_state(status="Stopped", running=False, continuing=False)
    #    self.ca.set_pv_value(wave_prefixed("START"), 1)
    #    self.check_running_state(status="Running", running=True, continuing=True)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_GIVEN_the_waveform_generator_is_stopped_WHEN_it_is_aborted_THEN_it_is_stopped(self):
    #    self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_STOPPED])
    #    self.check_running_state(status="Stopped", running=False, continuing=False)
    #    self.ca.set_pv_value(wave_prefixed("ABORT"), 1)
    #    self.check_running_state(status="Stopped", running=False, continuing=False)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_GIVEN_the_waveform_generator_is_stopped_WHEN_it_is_stopped_THEN_it_is_stopped(self):
    #    self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_STOPPED])
    #    self.check_running_state(status="Stopped", running=False, continuing=False)
    #    self.ca.set_pv_value(wave_prefixed("STOP"), 1)
    #    self.check_running_state(status="Stopped", running=False, continuing=False)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_GIVEN_the_waveform_generator_is_running_WHEN_it_is_started_THEN_it_is_running(self):
    #    self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_RUNNING])
    #    self.check_running_state(status="Running", running=True, continuing=True)
    #    self.ca.set_pv_value(wave_prefixed("START"), 1)
    #    self.check_running_state(status="Running", running=True, continuing=True)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_GIVEN_the_waveform_generator_is_running_WHEN_it_is_aborted_THEN_it_is_aborted(self):
    #    self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_RUNNING])
    #    self.check_running_state(status="Running", running=True, continuing=True)
    #    self.ca.set_pv_value(wave_prefixed("ABORT"), 1)
    #    self.check_running_state(status="Aborted", running=False, continuing=False)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_GIVEN_the_waveform_generator_is_running_WHEN_it_is_stopped_THEN_it_is_finishing_and_then_stops_within_5_seconds(self):
    #    self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_RUNNING])
    #    self.check_running_state(status="Running", running=True, continuing=True)
    #    self.ca.set_pv_value(wave_prefixed("STOP"), 1)
    #    self.check_running_state(status="Finishing", running=True, continuing=False)
    #    sleep(5)
    #    self.check_running_state(status="Stopped", running=False, continuing=False)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_GIVEN_the_waveform_generator_is_aborted_WHEN_it_is_started_THEN_it_is_running(self):
    #    self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_ABORTED])
    #    self.check_running_state(status="Aborted", running=False, continuing=False)
    #    self.ca.set_pv_value(wave_prefixed("START"), 1)
    #    self.check_running_state(status="Running", running=True, continuing=True)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_GIVEN_the_waveform_generator_is_aborted_WHEN_it_is_aborted_THEN_it_is_aborted(self):
    #    self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_ABORTED])
    #    self.check_running_state(status="Aborted", running=False, continuing=False)
    #    self.ca.set_pv_value(wave_prefixed("ABORT"), 1)
    #    self.check_running_state(status="Aborted", running=False, continuing=False)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_GIVEN_the_waveform_generator_is_aborted_WHEN_it_is_stopped_THEN_it_is_aborted(self):
    #    self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_ABORTED])
    #    self.check_running_state(status="Aborted", running=False, continuing=False)
    #    self.ca.set_pv_value(wave_prefixed("STOP"), 1)
    #    self.check_running_state(status="Aborted", running=False, continuing=False)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_GIVEN_the_waveform_generator_is_aborted_WHEN_it_is_stopped_THEN_it_is_aborted(self):
    #    self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_ABORTED])
    #    self.check_running_state(status="Aborted", running=False, continuing=False)
    #    self.ca.set_pv_value(wave_prefixed("STOP"), 1)
    #    self.check_running_state(status="Aborted", running=False, continuing=False)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_WHEN_waveform_type_is_set_THEN_the_device_reports_it_has_changed(self):
    #    for i in range(8):
    #        self.ca.set_pv_value(wave_prefixed("TYPE:SP"), i)
    #        self.ca.assert_that_pv_is(wave_prefixed("TYPE.RVAL"), i)
    #
    #@skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    #def test_GIVEN_multiple_channels_WHEN_waveform_frequency_is_set_THEN_the_device_is_updated_to_that_value(self):
    #    expected_values = [123.456, 789.012, 345.678]
    #    assert len(expected_values) == NUMBER_OF_CHANNELS
    #
    #    for channel in range(NUMBER_OF_CHANNELS):
    #        self.ca.set_pv_value(prefixed("CHANNEL:SP.VAL"), channel)
    #        self.ca.set_pv_value(wave_prefixed("FREQ:SP"), expected_values[channel])
    #    for channel in range(NUMBER_OF_CHANNELS):
    #        self.ca.set_pv_value(prefixed("CHANNEL:SP.VAL"), channel)
    #        self.ca.assert_that_pv_is(wave_prefixed("FREQ"), expected_values[channel])

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_multiple_channels_WHEN_waveform_amplitude_is_set_THEN_the_device_is_updated_to_that_value_with_channel_conversion_factor_applied(self):
        input_values = [123.456, 789.012, 345.678]
        conversion_factors = [
            float(self.ca.get_pv_value(prefixed("POS:SCALE")))*1000.0,
            float(self.ca.get_pv_value(prefixed("STRESS:SCALE")))*float(self.ca.get_pv_value(prefixed("STRESS:AREA"))),
            float(self.ca.get_pv_value(prefixed("STRAIN:SCALE")))*100000.0/float(self.ca.get_pv_value(prefixed("STRAIN:LENGTH")))
        ]
        expected_values = [input_values[i]/conversion_factors[i] for i in range(NUMBER_OF_CHANNELS)]
        assert len(expected_values) == len(conversion_factors) == len(input_values) == NUMBER_OF_CHANNELS

        for channel in range(NUMBER_OF_CHANNELS):
            self.ca.set_pv_value(prefixed("CHANNEL:SP.VAL"), channel)
            self.ca.set_pv_value(wave_prefixed("AMP:SP"), input_values[channel])
        for channel in range(NUMBER_OF_CHANNELS):
            self.ca.set_pv_value(prefixed("CHANNEL:SP.VAL"), channel)
            self.ca.assert_that_pv_is_number(wave_prefixed("AMP"), expected_values[channel], tolerance=0.0005)
