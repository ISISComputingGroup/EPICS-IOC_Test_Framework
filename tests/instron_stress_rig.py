import unittest
from unittest import skipIf

import time

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

import math

RAMP_WAVEFORM_TYPES = ["Ramp", "Dual ramp", "Trapezium", "Absolute ramp", "Absolute hold ramp",
                            "Absolute rate ramp"]

POS_STRESS_STRAIN = ["POS", "STRESS", "STRAIN"]

class Instron_stress_rigTests(unittest.TestCase):
    """
    Tests for the Instron IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("instron_stress_rig")

        self.ca = ChannelAccess(15)
        self.ca.wait_for("INSTRON_01:CHANNEL", timeout=30)

        # Set device types correctly if we're in devsim mode.
        # Can't use lewis backdoor commands in recsim so this won't work.
        if not IOCRegister.uses_rec_sim:
            for index, chan_type2 in enumerate((3, 2, 4)):
                self._lewis.backdoor_command(["device", "set_channel_param", str(index + 1), "channel_type", str(chan_type2)])

            self.ca.assert_that_pv_is("INSTRON_01:CHANNEL:SP.ZRST", "Position")
            self.ca.set_pv_value("INSTRON_01:CHANNEL:SP", 0)

    def test_WHEN_the_rig_is_initialized_THEN_the_status_is_ok(self):
        self.ca.assert_that_pv_is("INSTRON_01:STAT:DISP", "System OK")

    def test_WHEN_the_rig_is_initialized_THEN_it_is_not_going(self):
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "NO")

    def test_WHEN_the_rig_is_initialized_THEN_it_is_not_panic_stopping(self):
        self.ca.assert_that_pv_is("INSTRON_01:PANIC:SP", "READY")

    def test_WHEN_the_rig_is_initialized_THEN_it_is_not_stopping(self):
        self.ca.assert_that_pv_is("INSTRON_01:STOP:SP", "READY")

    def test_that_the_rig_is_not_normally_in_control_mode(self):
        self.ca.assert_that_pv_is("INSTRON_01:STOP:SP", "READY")

    def test_WHEN_init_sequence_run_THEN_waveform_ramp_is_set_the_status_is_ok(self):
        for chan in POS_STRESS_STRAIN:
            self.ca.set_pv_value("INSTRON_01:{0}:RAMP:WFTYP:SP".format(chan), 0)

        self.ca.set_pv_value("INSTRON_01:INIT", 1)

        for chan in POS_STRESS_STRAIN:
            self.ca.assert_that_pv_is("INSTRON_01:{0}:RAMP:WFTYP".format(chan), RAMP_WAVEFORM_TYPES[3])

    def _switch_to_position_channel_and_change_setpoint(self):
        # Select position as control channel
        self.ca.set_pv_value("INSTRON_01:CHANNEL:SP", 0)
        self.ca.assert_that_pv_is("INSTRON_01:CHANNEL", "Position")
        # Change the setpoint so that movement can be started
        current_setpoint = float(self.ca.get_pv_value("INSTRON_01:POS:SP"))
        self.ca.set_pv_value("INSTRON_01:POS:SP", current_setpoint + 123456)
        self.ca.assert_that_pv_is_number("INSTRON_01:POS:SP:RBV", current_setpoint + 123456, tolerance=1)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_going_and_then_stopping_THEN_going_pv_reflects_the_expected_state(self):
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "NO")
        self._switch_to_position_channel_and_change_setpoint()
        self.ca.set_pv_value("INSTRON_01:MOVE:GO:SP", 1)
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "YES")
        self.ca.set_pv_value("INSTRON_01:STOP:SP", 1)
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "NO")
        self.ca.set_pv_value("INSTRON_01:STOP:SP", 0)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_going_and_then_panic_stopping_THEN_going_pv_reflects_the_expected_state(self):
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "NO")
        self._switch_to_position_channel_and_change_setpoint()
        self.ca.set_pv_value("INSTRON_01:MOVE:GO:SP", 1)
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "YES")
        self.ca.set_pv_value("INSTRON_01:PANIC:SP", 1)
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "NO")
        self.ca.set_pv_value("INSTRON_01:PANIC:SP", 0)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_arbitrary_command_Q22_is_sent_THEN_the_response_is_a_status_code(self):
        self.ca.set_pv_value("INSTRON_01:ARBITRARY:SP", "Q22")
        # Assert that the response to Q22 is a status code
        self.ca.assert_that_pv_is_an_integer_between("INSTRON_01:ARBITRARY", min=0, max=65535)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_arbitrary_command_Q300_is_sent_THEN_the_response_is_a_number_between_1_and_3(self):
        self.ca.set_pv_value("INSTRON_01:ARBITRARY:SP", "Q300")
        # Assert that the response to Q300 is between 1 and 3
        self.ca.assert_that_pv_is_an_integer_between("INSTRON_01:ARBITRARY", min=1, max=3)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_arbitrary_command_C4_is_sent_THEN_Q4_gives_back_the_value_that_was_just_set(self):

        def _set_and_check(value):
            self.ca.set_pv_value("INSTRON_01:ARBITRARY:SP", "C4,1," + str(value))
            self.ca.assert_that_pv_is("INSTRON_01:ARBITRARY:SP", "C4,1," + str(value))
            self.ca.set_pv_value("INSTRON_01:ARBITRARY:SP", "Q4,1")
            self.ca.assert_that_pv_is_number("INSTRON_01:ARBITRARY", value, tolerance=0.0001)

        for v in [0, 1, 0]:
            _set_and_check(v)

    def test_WHEN_control_channel_is_requested_THEN_an_allowed_value_is_returned(self):
        self.ca.assert_that_pv_is_one_of("INSTRON_01:CHANNEL", ["Stress", "Strain", "Position"])

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_control_channel_setpoint_is_requested_THEN_it_is_one_of_the_allowed_values(self):
        self.ca.assert_that_pv_is_one_of("INSTRON_01:CHANNEL:SP", ["Stress", "Strain", "Position"])

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_the_control_channel_is_set_THEN_the_readback_contains_the_value_that_was_just_set(self):
        for set_val, return_val in [(0, "Position"), (1, "Stress"), (2, "Strain")]:
            self.ca.assert_setting_setpoint_sets_readback(set_val, "INSTRON_01:CHANNEL", expected_value=return_val, timeout=30)

    def test_WHEN_the_step_time_for_various_channels_is_set_as_an_integer_THEN_the_readback_contains_the_value_that_was_just_set(
            self):
        for chan, val in [("POS", 123), ("STRESS", 456), ("STRAIN", 789)]:
            pv_name = "INSTRON_01:" + chan + ":STEP:TIME"
            self.ca.assert_setting_setpoint_sets_readback(val, pv_name)

    def test_WHEN_the_step_time_for_various_channels_is_set_as_a_float_THEN_the_readback_contains_the_value_that_was_just_set(
            self):
        for chan, val in [("POS", 111.111), ("STRESS", 222.222), ("STRAIN", 333.333)]:
            pv_name = "INSTRON_01:" + chan + ":STEP:TIME"
            self.ca.assert_setting_setpoint_sets_readback(val, pv_name)

    def test_WHEN_the_ramp_waveform_for_a_channel_is_set_THEN_the_readback_contains_the_value_that_was_just_set(self):
        pv_name = "INSTRON_01:{0}:RAMP:WFTYP"
        for chan in POS_STRESS_STRAIN:
            for set_value, return_value in enumerate(RAMP_WAVEFORM_TYPES):
                self.ca.assert_setting_setpoint_sets_readback(set_value, pv_name.format(chan), expected_value=return_value)

    def test_WHEN_the_ramp_amplitude_for_a_channel_is_set_as_an_integer_THEN_the_readback_contains_the_value_that_was_just_set(self):
        for chan in POS_STRESS_STRAIN:
            for val in [0, 10, 1000, 1000000]:
                pv_name = "INSTRON_01:" + chan + ":RAW:SP"
                pv_name_rbv = pv_name + ":RBV"
                self.ca.assert_setting_setpoint_sets_readback(val, readback_pv=pv_name_rbv, set_point_pv=pv_name)

    def test_WHEN_the_ramp_amplitude_for_a_channel_is_set_as_a_float_THEN_the_readback_contains_the_value_that_was_just_set(self):
        for chan in POS_STRESS_STRAIN:
            for val in [1.0, 5.5, 1.000001, 9.999999, 10000.1]:
                pv_name = "INSTRON_01:" + chan + ":RAW:SP"
                pv_name_rbv = pv_name + ":RBV"
                self.ca.assert_setting_setpoint_sets_readback(val, readback_pv=pv_name_rbv, set_point_pv=pv_name)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_the_setpoint_for_a_channel_is_set_THEN_the_readback_contains_the_value_that_was_just_set(self):
        def _set_and_check(chan, value):
            self.ca.set_pv_value("INSTRON_01:" + chan + ":SP", value)
            self.ca.assert_that_pv_is_number("INSTRON_01:" + chan + ":SP", value, tolerance=0.001)
            self.ca.assert_that_pv_is_number("INSTRON_01:" + chan + ":SP:RBV", value, tolerance=0.05)

        # Ensure stress area and strain length are sensible values (i.e. not zero)
        self._lewis.backdoor_command(["device", "set_channel_param", "2", "area", "10"])
        self._lewis.backdoor_command(["device", "set_channel_param", "3", "length", "10"])

        self.ca.assert_that_pv_is_number("INSTRON_01:STRESS:AREA", 10, tolerance=0.001)
        self.ca.assert_that_pv_is_number("INSTRON_01:STRAIN:LENGTH", 10, tolerance=0.001)

        for chan in POS_STRESS_STRAIN:
            for i in [1.0, 123.456, 555.555, 1000]:
                _set_and_check(chan, i)

    def test_WHEN_channel_tolerance_is_set_THEN_it_changes_limits_on_SP_RBV(self):
        for chan in POS_STRESS_STRAIN:
            sp_val = 1
            self.ca.set_pv_value("INSTRON_01:" + chan + ":SP", sp_val)
            for val in [0.1, 1.0, 2.5]:
                pv_name = "INSTRON_01:" + chan + ":TOLERANCE"
                pv_name_high = "INSTRON_01:" + chan + ":SP:RBV.HIGH"
                pv_name_low = "INSTRON_01:" + chan + ":SP:RBV.LOW"
                self.ca.assert_setting_setpoint_sets_readback(val, readback_pv=pv_name_high, set_point_pv=pv_name, expected_value=val+sp_val, expected_alarm=None)
                self.ca.assert_setting_setpoint_sets_readback(val, readback_pv=pv_name_low, set_point_pv=pv_name,
                                                              expected_value=sp_val - val, expected_alarm=None)

    def test_GIVEN_a_big_tolerance_WHEN_the_setpoint_is_set_THEN_the_setpoint_has_no_alarms(self):
        def _set_and_check(chan, value):
            self.ca.set_pv_value("INSTRON_01:" + chan + ":SP", value)
            self.ca.set_pv_value("INSTRON_01:" + chan + ":TOLERANCE", 9999)
            self.ca.assert_pv_alarm_is("INSTRON_01:" + chan + ":SP:RBV", ChannelAccess.ALARM_NONE)

        for chan in POS_STRESS_STRAIN:
            for i in [0.123, 567]:
                _set_and_check(chan, i)

    def test_GIVEN_a_tolerance_of_minus_one_WHEN_the_setpoint_is_set_THEN_the_setpoint_readback_has_alarms(
            self):
        def _set_and_check(chan, value):
            self.ca.set_pv_value("INSTRON_01:" + chan + ":SP", value)
            self.ca.set_pv_value("INSTRON_01:" + chan + ":TOLERANCE", -1)
            self.ca.assert_pv_alarm_is("INSTRON_01:" + chan + ":SP:RBV", ChannelAccess.ALARM_MINOR)

        for chan in POS_STRESS_STRAIN:
            for i in [0.234, 789]:
                _set_and_check(chan, i)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_ioc_gets_a_raw_position_reading_from_the_device_THEN_it_is_converted_correctly(self):

        # Rig must be stopped for this test to work
        if self.ca.get_pv_value("INSTRON_01:GOING") != "NO":
            self.ca.set_pv_value("INSTRON_01:STOP:SP", 1)

        self.ca.assert_that_pv_is("INSTRON_01:GOING", "NO")

        for chan_scale in [0.1, 10.0]:
            self._lewis.backdoor_command(["device", "set_channel_param", "1", "scale", str(chan_scale)])
            self.ca.assert_that_pv_is("INSTRON_01:POS:SCALE", chan_scale)

            for raw_value in [0, 123]:
                self._lewis.backdoor_command(["device", "set_channel_param", "1", "value", str(raw_value)])
                self.ca.assert_that_pv_is_number("INSTRON_01:POS:RAW", raw_value, tolerance=0.01)
                self.ca.assert_that_pv_is_number("INSTRON_01:POS", raw_value * chan_scale * 1000,
                                                 tolerance=(0.01 * chan_scale * 1000))

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_ioc_gets_a_raw_stress_reading_from_the_device_THEN_it_is_converted_correctly(self):

        for chan_area in [0.1, 10.0]:
            self._lewis.backdoor_command(["device", "set_channel_param", "2", "area", str(chan_area)])
            self.ca.assert_that_pv_is("INSTRON_01:STRESS:AREA", chan_area)

            for chan_scale in [0.1, 10.0]:
                self._lewis.backdoor_command(["device", "set_channel_param", "2", "scale", str(chan_scale)])
                self.ca.assert_that_pv_is("INSTRON_01:STRESS:SCALE", chan_scale)

                for raw_value in [0, 123]:
                    self._lewis.backdoor_command(["device", "set_channel_param", "2", "value", str(raw_value)])
                    self.ca.assert_that_pv_is("INSTRON_01:STRESS:RAW", raw_value)
                    self.ca.assert_that_pv_is("INSTRON_01:STRESS", raw_value * chan_scale * (1.0/chan_area))

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_strain_length_updates_on_device_THEN_pv_updates(self):
        for value in [1,123]:
            self._lewis.backdoor_command(["device", "set_channel_param", "3", "length", str(value)])
            self.ca.assert_that_pv_is("INSTRON_01:STRAIN:LENGTH", value)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_ioc_gets_a_raw_strain_reading_from_the_device_THEN_it_is_converted_correctly(self):
        for chan_scale in [0.1, 10.0]:
            self._lewis.backdoor_command(["device", "set_channel_param", "3", "scale", str(chan_scale)])

            for chan_length in [0.1, 10.0]:
                self._lewis.backdoor_command(["device", "set_channel_param", "3", "length", str(chan_length)])

                for raw_value in [0, 0.001]:
                    self._lewis.backdoor_command(["device", "set_channel_param", "3", "value", str(raw_value)])

                    self.ca.assert_that_pv_is("INSTRON_01:STRAIN:SCALE", chan_scale)
                    self.ca.assert_that_pv_is("INSTRON_01:STRAIN:LENGTH", chan_length)
                    self.ca.assert_that_pv_is("INSTRON_01:STRAIN:RAW", raw_value)

                    self.ca.assert_that_pv_is("INSTRON_01:STRAIN", (raw_value * chan_scale * 100000 * (1/chan_length)))

    def test_WHEN_the_area_setpoint_is_set_THEN_the_area_readback_updates(self):
        def _set_and_check(value):
            self.ca.set_pv_value("INSTRON_01:STRESS:AREA:SP", value)
            self.ca.assert_that_pv_is("INSTRON_01:STRESS:AREA", value)
            self.ca.assert_pv_alarm_is("INSTRON_01:STRESS:AREA", ChannelAccess.ALARM_NONE)

        for val in [0.234, 789]:
            _set_and_check(val)

    def test_WHEN_the_area_setpoint_is_set_THEN_the_diameter_readback_updates(self):
        def _set_and_check(value):
            self.ca.set_pv_value("INSTRON_01:STRESS:AREA:SP", value)
            self.ca.assert_that_pv_is("INSTRON_01:STRESS:DIAMETER", (2*math.sqrt(value/math.pi)))
            self.ca.assert_pv_alarm_is("INSTRON_01:STRESS:DIAMETER", ChannelAccess.ALARM_NONE)

        for val in [0.234, 789]:
            _set_and_check(val)

    def test_WHEN_the_diameter_setpoint_is_set_THEN_the_diameter_readback_updates(self):
        def _set_and_check(value):
            self.ca.set_pv_value("INSTRON_01:STRESS:DIAMETER:SP", value)
            self.ca.assert_that_pv_is_number("INSTRON_01:STRESS:DIAMETER", value, tolerance=0.0005)
            self.ca.assert_pv_alarm_is("INSTRON_01:STRESS:DIAMETER", ChannelAccess.ALARM_NONE)

        for val in [0.234, 789]:
            _set_and_check(val)

    def test_WHEN_the_diameter_setpoint_is_set_THEN_the_area_readback_updates(self):
        def _set_and_check(value):
            self.ca.set_pv_value("INSTRON_01:STRESS:DIAMETER:SP", value)
            self.ca.assert_that_pv_is_number("INSTRON_01:STRESS:AREA", ((value/2.0)**2 * math.pi), tolerance=0.0005)
            self.ca.assert_pv_alarm_is("INSTRON_01:STRESS:AREA", ChannelAccess.ALARM_NONE)

        for val in [0.234, 789]:
            _set_and_check(val)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_a_position_setpoint_is_set_THEN_it_is_converted_correctly(self):
        for scale in [2.34, 456.78]:
            self._lewis.backdoor_command(["device", "set_channel_param", "1", "scale", str(scale)])
            self.ca.assert_that_pv_is("INSTRON_01:POS:SCALE", scale)

            for val in [1.23, 123.45]:
                self.ca.set_pv_value("INSTRON_01:POS:SP", val)
                self.ca.assert_that_pv_is_number("INSTRON_01:POS:RAW:SP", val * (1.0/1000.0) * (1/scale), tolerance=0.0000000001)
                self.ca.assert_pv_alarm_is("INSTRON_01:POS:RAW:SP", ChannelAccess.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_a_stress_setpoint_is_set_THEN_it_is_converted_correctly(self):

        for area in [789, 543.21]:
            self._lewis.backdoor_command(["device", "set_channel_param", "2", "area", str(area)])
            self.ca.assert_that_pv_is("INSTRON_01:STRESS:AREA", area)

            for chan_scale in [2.34, 456.78]:
                self._lewis.backdoor_command(["device", "set_channel_param", "2", "scale", str(chan_scale)])
                self.ca.assert_that_pv_is("INSTRON_01:STRESS:SCALE", chan_scale)

                for val in [1.23, 123.45]:
                    self.ca.set_pv_value("INSTRON_01:STRESS:SP", val)
                    self.ca.assert_that_pv_is_number("INSTRON_01:STRESS:RAW:SP", val * (1 / chan_scale) * area,
                                                     tolerance=0.0000000001)
                    self.ca.assert_pv_alarm_is("INSTRON_01:STRESS:RAW:SP", ChannelAccess.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_a_strain_setpoint_is_set_THEN_it_is_converted_correctly(self):

        for length in [789, 543.21]:
            self._lewis.backdoor_command(["device", "set_channel_param", "3", "length", str(length)])
            self.ca.assert_that_pv_is("INSTRON_01:STRAIN:LENGTH", length)

            for chan_scale in [2.34, 456.78]:
                self._lewis.backdoor_command(["device", "set_channel_param", "3", "scale", str(chan_scale)])
                self.ca.assert_that_pv_is("INSTRON_01:STRAIN:SCALE", chan_scale)

                for val in [1.23, 123.45]:
                    self.ca.set_pv_value("INSTRON_01:STRAIN:SP", val)
                    self.ca.assert_that_pv_is_number("INSTRON_01:STRAIN:RAW:SP", val * (1 / chan_scale) * length * (1.0/100000.0),
                                                     tolerance=0.0000000001)
                    self.ca.assert_pv_alarm_is("INSTRON_01:STRAIN:RAW:SP", ChannelAccess.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_the_channel_type_updates_on_the_device_THEN_the_pv_updates(self):

        for chan_name, chan_num in [("POS", 1), ("STRESS", 2), ("STRAIN", 3)]:
            for value_1, value_2, return_value_1, return_value_2 in [
                    (0, 1, "Standard transducer", "Unrecognized"),
                    (1, 10, "User transducer", "Ext. waveform generator")]:

                self._lewis.backdoor_command(["device", "set_channel_param", str(chan_num), "transducer_type", str(value_1)])
                self._lewis.backdoor_command(["device", "set_channel_param", str(chan_num), "channel_type", str(value_2)])
                self.ca.assert_that_pv_is("INSTRON_01:"+chan_name+":TYPE:STANDARD",return_value_1 )
                self.ca.assert_that_pv_is("INSTRON_01:"+chan_name+":TYPE", return_value_2)

    def test_WHEN_waveform_type_abs_set_on_axes_THEN_all_axes_are_set(self):
        def _set_and_check(set_value, return_value):
            self.ca.set_pv_value("INSTRON_01:AXES:RAMP:WFTYP:SP", set_value)
            for chan in POS_STRESS_STRAIN:
                self.ca.assert_that_pv_is("INSTRON_01:{0}:RAMP:WFTYP".format(chan), return_value)
                self.ca.assert_pv_alarm_is("INSTRON_01:{0}:RAMP:WFTYP".format(chan), ChannelAccess.ALARM_NONE)

        for set_value, return_value in enumerate(RAMP_WAVEFORM_TYPES):
            _set_and_check(set_value, return_value)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_channel_fails_check_THEN_channel_mbbi_record_is_invalid_and_has_tag_disabled(self):

        for index, (chan_name, type, index_as_name, channel_as_name) in enumerate(zip(POS_STRESS_STRAIN, (1, 1, 1), ("ZR", "ON", "TW"), ("Position", "Stress", "Strain"))):

            self._lewis.backdoor_command(["device", "set_channel_param", str(index + 1), "channel_type", str(type)])

            self.ca.assert_that_pv_is("INSTRON_01:"+chan_name+":TYPE:CHECK", "FAIL")
            self.ca.assert_that_pv_is("INSTRON_01:CHANNEL:SP.{}ST".format(index_as_name),
                                      "{0} - disabled".format(channel_as_name))

            self.ca.set_pv_value("INSTRON_01:CHANNEL:SP", index)

            self.ca.assert_pv_alarm_is("INSTRON_01:CHANNEL:SP", ChannelAccess.ALARM_INVALID)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_channel_succeeds_check_THEN_channel_mbbi_record_is_invalid_and_has_tag_disabled(self):
        self.ca.set_pv_value("INSTRON_01:CHANNEL:SP", 3)
        for index, (chan_name, type, index_as_name, channel_as_name) in enumerate(zip(POS_STRESS_STRAIN, (3, 2, 4), ("ZR", "ON", "TW"), ("Position", "Stress", "Strain"))):

            self._lewis.backdoor_command(["device", "set_channel_param", str(index + 1), "channel_type", str(type)])

            self.ca.assert_that_pv_is("INSTRON_01:"+chan_name+":TYPE:CHECK", "PASS", timeout=30)

            self.ca.assert_that_pv_is("INSTRON_01:CHANNEL:SP.{}ST".format(index_as_name), channel_as_name)
            self.ca.assert_that_pv_is("INSTRON_01:CHANNEL:SP.{}SV".format(index_as_name), ChannelAccess.ALARM_NONE)

            self.ca.set_pv_value("INSTRON_01:CHANNEL:SP", index)

            self.ca.assert_pv_alarm_is("INSTRON_01:CHANNEL:SP", ChannelAccess.ALARM_NONE)
