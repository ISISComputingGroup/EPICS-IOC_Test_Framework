import unittest
import math
import time

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


# Device prefix
DEVICE_PREFIX = "INSTRON_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("INSTRON"),
        "macros": {},
        "emulator": "instron_stress_rig",
        "emulator_protocol": "stream",
    },
]

RAMP_WAVEFORM_TYPES = ["Ramp", "Dual ramp", "Trapezium", "Absolute ramp", "Absolute hold ramp",
                       "Absolute rate ramp"]

POS_STRESS_STRAIN = ["POS", "STRESS", "STRAIN"]
NUMBER_OF_CHANNELS = len(POS_STRESS_STRAIN)
WAVEFORM_STOPPED = "0"
WAVEFORM_RUNNING = "1"
WAVEFORM_ABORTED = "4"
WAVEFORM_HOLDING = "2"
WAVEFORM_FINISHING = "3"
LOTS_OF_CYCLES = 999999
CHANNELS = {"Position": 1, "Stress": 2, "Strain": 3}


def add_prefix(prefix, root):
    return "{0}:{1}".format(prefix, root)


def wave_prefixed(val):
    return add_prefix("WAVE", val)


def quart_prefixed(val):
    return add_prefix("QUART", val)


class InstronStressRigTests(unittest.TestCase):
    """
    Tests for the Instron IOC.
    """

    def _change_channel(self, name):
        # Setpoint is zero-indexed
        self.ca.set_pv_value("CHANNEL:SP", CHANNELS[name] - 1)
        self.ca.assert_that_pv_is("CHANNEL.RVAL", CHANNELS[name])
        self.ca.assert_pv_alarm_is("CHANNEL", self.ca.ALARM_NONE)
        self.ca.assert_that_pv_is("CHANNEL:GUI", name)
        self.ca.assert_pv_alarm_is("CHANNEL:GUI", self.ca.ALARM_NONE)

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("instron_stress_rig", DEVICE_PREFIX)

        self.ca = ChannelAccess(15, device_prefix=DEVICE_PREFIX)
        self.ca.wait_for("CHANNEL", timeout=30)

        # Can't use lewis backdoor commands in recsim
        # All of the below commands apply to devsim only.
        if not IOCRegister.uses_rec_sim:
            # Reinitialize the emulator state
            self._lewis.backdoor_command(["device", "reset"])

            self._lewis.backdoor_set_on_device("status", 7680)

            for index, chan_type2 in enumerate((3, 2, 4)):
                self._lewis.backdoor_command(["device", "set_channel_param", str(index + 1),
                                              "channel_type", str(chan_type2)])

            self.ca.assert_that_pv_is("CHANNEL:SP.ZRST", "Position")

            self._change_channel("Position")

            # Ensure the rig is stopped
            self._lewis.backdoor_command(["device", "movement_type", "0"])
            self.ca.assert_that_pv_is("GOING", "NO")

            # Ensure stress area and strain length are sensible values (i.e. not zero)
            self._lewis.backdoor_command(["device", "set_channel_param", "2", "area", "10"])
            self._lewis.backdoor_command(["device", "set_channel_param", "3", "length", "10"])
            self.ca.assert_that_pv_is_number("STRESS:AREA", 10, tolerance=0.001)
            self.ca.assert_that_pv_is_number("STRAIN:LENGTH", 10, tolerance=0.001)

            # Ensure that all the scales are sensible values (i.e. not zero)
            for index, channel in enumerate(POS_STRESS_STRAIN, 1):
                self._lewis.backdoor_command(["device", "set_channel_param", str(index), "scale", "10"])
                self.ca.assert_that_pv_is_number(channel + ":SCALE", 10, tolerance=0.001)

            # Always set the waveform generator to run for lots of cycles so it only stops if we want it to
            self.ca.set_pv_value(quart_prefixed("CYCLE:SP"), LOTS_OF_CYCLES)

    @skip_if_recsim("In rec sim we can not set the code easily")
    def test_WHEN_the_rig_has_no_error_THEN_the_status_is_ok(self):
        self._lewis.backdoor_set_on_device("status", 7680)

        self.ca.assert_that_pv_is("STAT:DISP", "System OK")
        self.ca.assert_pv_alarm_is("STAT:DISP", ChannelAccess.ALARM_NONE)

    @skip_if_recsim("In rec sim we can not set the code easily")
    def test_WHEN_the_rig_has_other_no_error_THEN_the_status_is_ok(self):
        self._lewis.backdoor_set_on_device("status", 0)

        self.ca.assert_that_pv_is("STAT:DISP", "System OK")
        self.ca.assert_pv_alarm_is("STAT:DISP", ChannelAccess.ALARM_NONE)

    @skip_if_recsim("In rec sim we can not set the code easily")
    def test_WHEN_the_rig_has_error_THEN_the_status_is_emergency_stop_pushed(self):
        code_and_errors = [
            ([0, 1, 1, 0], "Emergency stop pushed"),
            ([0, 0, 0, 1], "Travel limit exceeded"),
            ([0, 0, 1, 0], "Power amplifier too hot"),
            ([0, 1, 1, 0], "Emergency stop pushed"),
            ([0, 1, 0, 1], "Invalid status from rig"),
            ([0, 1, 0, 0], "Invalid status from rig"),
            ([0, 1, 1, 0], "Emergency stop pushed"),
            ([0, 1, 1, 1], "Oil too hot"),
            ([1, 0, 0, 0], "Oil level too low"),
            ([1, 0, 0, 1], "Motor too hot"),
            ([1, 0, 1, 0], "Oil pressure too high"),
            ([1, 0, 1, 1], "Oil pressure too low"),
            ([1, 1, 0, 0], "Manifold/pump blocked"),
            ([1, 1, 0, 1], "Oil level going too low"),
            ([1, 1, 1, 0], "Manifold low pressure")
        ]

        for code, error in code_and_errors:
            code_val = code[0] * 2 ** 12
            code_val += code[1] * 2 ** 11
            code_val += code[2] * 2 ** 10
            code_val += code[3] * 2 ** 9

            self._lewis.backdoor_set_on_device("status", code_val)

            self.ca.assert_that_pv_is("STAT:DISP", error, msg="code set {0} = {code_val}".format(code, code_val=code_val))
            self.ca.assert_pv_alarm_is("STAT:DISP", ChannelAccess.ALARM_MAJOR)

    def test_WHEN_the_rig_is_initialized_THEN_it_is_not_going(self):
        self.ca.assert_that_pv_is("GOING", "NO")

    def test_WHEN_the_rig_is_initialized_THEN_it_is_not_panic_stopping(self):
        self.ca.assert_that_pv_is("PANIC:SP", "READY")

    def test_WHEN_the_rig_is_initialized_THEN_it_is_not_stopping(self):
        self.ca.assert_that_pv_is("STOP:SP", "READY")

    def test_that_the_rig_is_not_normally_in_control_mode(self):
        self.ca.assert_that_pv_is("STOP:SP", "READY")

    def test_WHEN_init_sequence_run_THEN_waveform_ramp_is_set_the_status_is_ok(self):
        for chan in POS_STRESS_STRAIN:
            self.ca.set_pv_value("{0}:RAMP:WFTYP:SP".format(chan), 0)

        self.ca.set_pv_value("INIT", 1)

        for chan in POS_STRESS_STRAIN:
            self.ca.assert_that_pv_is("{0}:RAMP:WFTYP".format(chan), RAMP_WAVEFORM_TYPES[3])

    def _switch_to_position_channel_and_change_setpoint(self):

        # It has to be big or the set point will be reached before the test completes
        _big_set_point = 999999999999

        # Select position as control channel
        self._change_channel("Position")
        # Change the setpoint so that movement can be started
        self.ca.set_pv_value("POS:SP", _big_set_point)
        self.ca.assert_that_pv_is_number("POS:SP", _big_set_point, tolerance=1)
        self.ca.assert_that_pv_is_number("POS:SP:RBV", _big_set_point, tolerance=1)

    @skip_if_recsim("Dynamic behaviour not captured in RECSIM")
    def test_WHEN_going_and_then_stopping_THEN_going_pv_reflects_the_expected_state(self):
        self.ca.assert_that_pv_is("GOING", "NO")
        self._switch_to_position_channel_and_change_setpoint()
        self.ca.set_pv_value("MOVE:GO:SP", 1)
        self.ca.assert_that_pv_is("GOING", "YES")
        self.ca.set_pv_value("STOP:SP", 1)
        self.ca.assert_that_pv_is("GOING", "NO")
        self.ca.set_pv_value("STOP:SP", 0)

    @skip_if_recsim("Dynamic behaviour not captured in RECSIM")
    def test_WHEN_going_and_then_panic_stopping_THEN_going_pv_reflects_the_expected_state(self):
        self.ca.assert_that_pv_is("GOING", "NO")
        self._switch_to_position_channel_and_change_setpoint()
        self.ca.set_pv_value("MOVE:GO:SP", 1)
        self.ca.assert_that_pv_is("GOING", "YES")
        self.ca.set_pv_value("PANIC:SP", 1)
        self.ca.assert_that_pv_is("GOING", "NO")
        self.ca.set_pv_value("PANIC:SP", 0)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_arbitrary_command_Q22_is_sent_THEN_the_response_is_a_status_code(self):
        self.ca.set_pv_value("ARBITRARY:SP", "Q22")
        # Assert that the response to Q22 is a status code
        self.ca.assert_that_pv_is_an_integer_between("ARBITRARY", min=0, max=65535)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_arbitrary_command_Q300_is_sent_THEN_the_response_is_a_number_between_1_and_3(self):
        self.ca.set_pv_value("ARBITRARY:SP", "Q300")
        # Assert that the response to Q300 is between 1 and 3
        self.ca.assert_that_pv_is_an_integer_between("ARBITRARY", min=1, max=3)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_arbitrary_command_C4_is_sent_THEN_Q4_gives_back_the_value_that_was_just_set(self):

        def _set_and_check(value):
            self.ca.set_pv_value("ARBITRARY:SP", "C4,1," + str(value))
            self.ca.assert_that_pv_is("ARBITRARY:SP", "C4,1," + str(value))
            # No response from arbitrary command causes record to be TIMEOUT INVALID - this is expected.
            self.ca.assert_pv_alarm_is("ARBITRARY", self.ca.ALARM_INVALID)
            self.ca.set_pv_value("ARBITRARY:SP", "Q4,1")
            self.ca.assert_that_pv_is_number("ARBITRARY", value, tolerance=0.001)

        for v in [0, 1, 0]:
            _set_and_check(v)

    def test_WHEN_control_channel_is_requested_THEN_an_allowed_value_is_returned(self):
        self.ca.assert_that_pv_is_one_of("CHANNEL", CHANNELS.keys())

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_control_channel_setpoint_is_requested_THEN_it_is_one_of_the_allowed_values(self):
        self.ca.assert_that_pv_is_one_of("CHANNEL:SP", CHANNELS.keys())

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_the_control_channel_is_set_THEN_the_readback_contains_the_value_that_was_just_set(self):
        for channel in CHANNELS.keys():
            # change channel function contains the relevant assertions.
            self._change_channel(channel)

    def test_WHEN_the_step_time_for_various_channels_is_set_as_an_integer_THEN_the_readback_contains_the_value_that_was_just_set(
            self):
        for chan, val in [("POS", 123), ("STRESS", 456), ("STRAIN", 789)]:
            pv_name = chan + ":STEP:TIME"
            self.ca.assert_setting_setpoint_sets_readback(val, pv_name)

    def test_WHEN_the_step_time_for_various_channels_is_set_as_a_float_THEN_the_readback_contains_the_value_that_was_just_set(
            self):
        for chan, val in [("POS", 111.111), ("STRESS", 222.222), ("STRAIN", 333.333)]:
            pv_name = chan + ":STEP:TIME"
            self.ca.assert_setting_setpoint_sets_readback(val, pv_name)

    def test_WHEN_the_ramp_waveform_for_a_channel_is_set_THEN_the_readback_contains_the_value_that_was_just_set(self):
        pv_name = "{0}:RAMP:WFTYP"
        for chan in POS_STRESS_STRAIN:
            for set_value, return_value in enumerate(RAMP_WAVEFORM_TYPES):
                self.ca.assert_setting_setpoint_sets_readback(set_value, pv_name.format(chan), expected_value=return_value)

    def test_WHEN_the_ramp_amplitude_for_a_channel_is_set_as_an_integer_THEN_the_readback_contains_the_value_that_was_just_set(self):
        for chan in POS_STRESS_STRAIN:
            for val in [0, 10, 1000, 1000000]:
                pv_name = chan + ":RAW:SP"
                pv_name_rbv = pv_name + ":RBV"
                self.ca.assert_setting_setpoint_sets_readback(val, readback_pv=pv_name_rbv, set_point_pv=pv_name)

    def test_WHEN_the_ramp_amplitude_for_a_channel_is_set_as_a_float_THEN_the_readback_contains_the_value_that_was_just_set(self):
        for chan in POS_STRESS_STRAIN:
            for val in [1.0, 5.5, 1.000001, 9.999999, 10000.1]:
                pv_name = chan + ":RAW:SP"
                pv_name_rbv = pv_name + ":RBV"
                self.ca.assert_setting_setpoint_sets_readback(val, readback_pv=pv_name_rbv, set_point_pv=pv_name)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_the_setpoint_for_a_channel_is_set_THEN_the_readback_contains_the_value_that_was_just_set(self):
        def _set_and_check(chan, value):
            self.ca.set_pv_value(chan + ":SP", value)
            self.ca.assert_that_pv_is_number(chan + ":SP", value, tolerance=0.001)
            self.ca.assert_that_pv_is_number(chan + ":SP:RBV", value, tolerance=0.05, timeout=30)

        for chan in POS_STRESS_STRAIN:
            for i in [1.0, 123.456, 555.555, 1000]:
                _set_and_check(chan, i)

    def test_WHEN_channel_tolerance_is_set_THEN_it_changes_limits_on_SP_RBV(self):
        for chan in POS_STRESS_STRAIN:
            sp_val = 1
            self.ca.set_pv_value(chan + ":SP", sp_val)
            for val in [0.1, 1.0, 2.5]:
                pv_name = chan + ":TOLERANCE"
                pv_name_high = chan + ":SP:RBV.HIGH"
                pv_name_low = chan + ":SP:RBV.LOW"
                self.ca.assert_setting_setpoint_sets_readback(val, readback_pv=pv_name_high, set_point_pv=pv_name,
                                                              expected_value=val+sp_val, expected_alarm=None)
                self.ca.assert_setting_setpoint_sets_readback(val, readback_pv=pv_name_low, set_point_pv=pv_name,
                                                              expected_value=sp_val - val, expected_alarm=None)

    def test_GIVEN_a_big_tolerance_WHEN_the_setpoint_is_set_THEN_the_setpoint_has_no_alarms(self):
        def _set_and_check(chan, value):
            self.ca.set_pv_value(chan + ":SP", value)
            self.ca.set_pv_value(chan + ":TOLERANCE", 9999)
            self.ca.assert_pv_alarm_is(chan + ":SP:RBV", ChannelAccess.ALARM_NONE)

        for chan in POS_STRESS_STRAIN:
            for i in [0.123, 567]:
                _set_and_check(chan, i)

    def test_GIVEN_a_tolerance_of_minus_one_WHEN_the_setpoint_is_set_THEN_the_setpoint_readback_has_alarms(
            self):
        def _set_and_check(chan, value):
            self.ca.set_pv_value(chan + ":SP", value)
            self.ca.set_pv_value(chan + ":TOLERANCE", -1)
            self.ca.assert_pv_alarm_is(chan + ":SP:RBV", ChannelAccess.ALARM_MINOR)

        for chan in POS_STRESS_STRAIN:
            for i in [0.234, 789]:
                _set_and_check(chan, i)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_ioc_gets_a_raw_position_reading_from_the_device_THEN_it_is_converted_correctly(self):

        for chan_scale in [0.1, 10.0]:
            self._lewis.backdoor_command(["device", "set_channel_param", "1", "scale", str(chan_scale)])
            self.ca.assert_that_pv_is("POS:SCALE", chan_scale)

            for raw_value in [0, 123]:
                self._lewis.backdoor_command(["device", "set_channel_param", "1", "value", str(raw_value)])
                self.ca.assert_that_pv_is_number("POS:RAW", raw_value, tolerance=0.01)
                self.ca.assert_that_pv_is_number("POS", raw_value * chan_scale * 1000,
                                                 tolerance=(0.01 * chan_scale * 1000))

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_ioc_gets_a_raw_stress_reading_from_the_device_THEN_it_is_converted_correctly(self):

        for chan_area in [0.1, 10.0]:
            self._lewis.backdoor_command(["device", "set_channel_param", "2", "area", str(chan_area)])
            self.ca.assert_that_pv_is("STRESS:AREA", chan_area)

            for chan_scale in [0.1, 10.0]:
                self._lewis.backdoor_command(["device", "set_channel_param", "2", "scale", str(chan_scale)])
                self.ca.assert_that_pv_is("STRESS:SCALE", chan_scale)

                for raw_value in [0, 123]:
                    self._lewis.backdoor_command(["device", "set_channel_param", "2", "value", str(raw_value)])
                    self.ca.assert_that_pv_is("STRESS:RAW", raw_value)
                    self.ca.assert_that_pv_is("STRESS", raw_value * chan_scale * (1.0/chan_area))

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_strain_length_updates_on_device_THEN_pv_updates(self):
        for value in [1, 123]:
            self._lewis.backdoor_command(["device", "set_channel_param", "3", "length", str(value)])
            self.ca.assert_that_pv_is("STRAIN:LENGTH", value)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_ioc_gets_a_raw_strain_reading_from_the_device_THEN_it_is_converted_correctly(self):
        for chan_scale in [0.1, 10.0]:
            self._lewis.backdoor_command(["device", "set_channel_param", "3", "scale", str(chan_scale)])

            for chan_length in [0.1, 10.0]:
                self._lewis.backdoor_command(["device", "set_channel_param", "3", "length", str(chan_length)])

                for raw_value in [0, 0.001]:
                    self._lewis.backdoor_command(["device", "set_channel_param", "3", "value", str(raw_value)])

                    self.ca.assert_that_pv_is("STRAIN:SCALE", chan_scale)
                    self.ca.assert_that_pv_is("STRAIN:LENGTH", chan_length)
                    self.ca.assert_that_pv_is("STRAIN:RAW", raw_value)

                    self.ca.assert_that_pv_is("STRAIN", (raw_value * chan_scale * 100000 * (1/chan_length)))

    def test_WHEN_the_area_setpoint_is_set_THEN_the_area_readback_updates(self):
        def _set_and_check(value):
            self.ca.set_pv_value("STRESS:AREA:SP", value)
            self.ca.assert_that_pv_is_number("STRESS:AREA", value, tolerance=0.01)
            self.ca.assert_pv_alarm_is("STRESS:AREA", ChannelAccess.ALARM_NONE)

        for val in [0.234, 789]:
            _set_and_check(val)

    def test_WHEN_the_area_setpoint_is_set_THEN_the_diameter_readback_updates(self):
        def _set_and_check(value):
            self.ca.set_pv_value("STRESS:AREA:SP", value)
            self.ca.assert_that_pv_is_number("STRESS:DIAMETER", (2*math.sqrt(value/math.pi)), tolerance=0.01)
            self.ca.assert_pv_alarm_is("STRESS:DIAMETER", ChannelAccess.ALARM_NONE)

        for val in [0.234, 789]:
            _set_and_check(val)

    def test_WHEN_the_diameter_setpoint_is_set_THEN_the_diameter_readback_updates(self):
        def _set_and_check(value):
            self.ca.set_pv_value("STRESS:DIAMETER:SP", value)
            self.ca.assert_that_pv_is_number("STRESS:DIAMETER", value, tolerance=0.0005)
            self.ca.assert_pv_alarm_is("STRESS:DIAMETER", ChannelAccess.ALARM_NONE)

        for val in [0.234, 789]:
            _set_and_check(val)

    def test_WHEN_the_diameter_setpoint_is_set_THEN_the_area_readback_updates(self):
        def _set_and_check(value):
            self.ca.set_pv_value("STRESS:DIAMETER:SP", value)
            self.ca.assert_that_pv_is_number("STRESS:AREA", ((value/2.0)**2 * math.pi), tolerance=0.0005)
            self.ca.assert_pv_alarm_is("STRESS:AREA", ChannelAccess.ALARM_NONE)

        for val in [0.234, 789]:
            _set_and_check(val)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_a_position_setpoint_is_set_THEN_it_is_converted_correctly(self):
        for scale in [2.34, 456.78]:
            self._lewis.backdoor_command(["device", "set_channel_param", "1", "scale", str(scale)])
            self.ca.assert_that_pv_is("POS:SCALE", scale)

            for val in [1.23, 123.45]:
                self.ca.set_pv_value("POS:SP", val)
                self.ca.assert_that_pv_is_number("POS:RAW:SP", val * (1.0/1000.0) * (1/scale), tolerance=0.0000000001)
                self.ca.assert_pv_alarm_is("POS:RAW:SP", ChannelAccess.ALARM_NONE)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_a_stress_setpoint_is_set_THEN_it_is_converted_correctly(self):

        for area in [789, 543.21]:
            self._lewis.backdoor_command(["device", "set_channel_param", "2", "area", str(area)])
            self.ca.assert_that_pv_is("STRESS:AREA", area)

            for chan_scale in [2.34, 456.78]:
                self._lewis.backdoor_command(["device", "set_channel_param", "2", "scale", str(chan_scale)])
                self.ca.assert_that_pv_is("STRESS:SCALE", chan_scale)

                for val in [1.23, 123.45]:
                    self.ca.set_pv_value("STRESS:SP", val)
                    self.ca.assert_that_pv_is_number("STRESS:RAW:SP", val * (1 / chan_scale) * area,
                                                     tolerance=0.0000000001)
                    self.ca.assert_pv_alarm_is("STRESS:RAW:SP", ChannelAccess.ALARM_NONE)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_a_strain_setpoint_is_set_THEN_it_is_converted_correctly(self):

        for length in [789, 543.21]:
            self._lewis.backdoor_command(["device", "set_channel_param", "3", "length", str(length)])
            self.ca.assert_that_pv_is("STRAIN:LENGTH", length)

            for chan_scale in [2.34, 456.78]:
                self._lewis.backdoor_command(["device", "set_channel_param", "3", "scale", str(chan_scale)])
                self.ca.assert_that_pv_is("STRAIN:SCALE", chan_scale)

                for val in [1.23, 123.45]:
                    self.ca.set_pv_value("STRAIN:SP", val)
                    self.ca.assert_that_pv_is_number("STRAIN:RAW:SP", val * (1 / chan_scale) * length * (1.0/100000.0),
                                                     tolerance=0.0000000001)
                    self.ca.assert_pv_alarm_is("STRAIN:RAW:SP", ChannelAccess.ALARM_NONE)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_the_channel_type_updates_on_the_device_THEN_the_pv_updates(self):

        for chan_name, chan_num in [("POS", 1), ("STRESS", 2), ("STRAIN", 3)]:
            for value_1, value_2, return_value_1, return_value_2 in [
                    (0, 1, "Standard transducer", "Unrecognized"),
                    (1, 10, "User transducer", "Ext. waveform generator")]:

                self._lewis.backdoor_command(["device", "set_channel_param",
                                              str(chan_num), "transducer_type", str(value_1)])
                self._lewis.backdoor_command(["device", "set_channel_param",
                                              str(chan_num), "channel_type", str(value_2)])
                self.ca.assert_that_pv_is(""+chan_name+":TYPE:STANDARD",return_value_1 )
                self.ca.assert_that_pv_is(""+chan_name+":TYPE", return_value_2)

    def test_WHEN_waveform_type_abs_set_on_axes_THEN_all_axes_are_set(self):
        def _set_and_check(set_value, return_value):
            self.ca.set_pv_value("AXES:RAMP:WFTYP:SP", set_value)
            for chan in POS_STRESS_STRAIN:
                self.ca.assert_that_pv_is("{0}:RAMP:WFTYP".format(chan), return_value)
                self.ca.assert_pv_alarm_is("{0}:RAMP:WFTYP".format(chan), ChannelAccess.ALARM_NONE)

        for set_value, return_value in enumerate(RAMP_WAVEFORM_TYPES):
            _set_and_check(set_value, return_value)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_channel_fails_check_THEN_channel_mbbi_record_is_invalid_and_has_tag_disabled(self):

        for index, (chan_name, type, index_as_name, channel_as_name) in enumerate(zip(POS_STRESS_STRAIN, (1, 1, 1), ("ZR", "ON", "TW"), ("Position", "Stress", "Strain"))):

            self._lewis.backdoor_command(["device", "set_channel_param", str(index + 1), "channel_type", str(type)])

            self.ca.assert_that_pv_is(""+chan_name+":TYPE:CHECK", "FAIL")
            self.ca.assert_that_pv_is("CHANNEL:SP.{}ST".format(index_as_name),
                                      "{0} - disabled".format(channel_as_name))

            self.ca.set_pv_value("CHANNEL:SP", index)

            self.ca.assert_pv_alarm_is("CHANNEL:SP", ChannelAccess.ALARM_INVALID)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_channel_succeeds_check_THEN_channel_mbbi_record_is_invalid_and_has_tag_disabled(self):
        self.ca.set_pv_value("CHANNEL:SP", 3)
        for index, (chan_name, type, index_as_name, channel_as_name) in enumerate(zip(POS_STRESS_STRAIN, (3, 2, 4), ("ZR", "ON", "TW"), ("Position", "Stress", "Strain"))):

            self._lewis.backdoor_command(["device", "set_channel_param", str(index + 1), "channel_type", str(type)])

            self.ca.assert_that_pv_is(""+chan_name+":TYPE:CHECK", "PASS", timeout=30)

            self.ca.assert_that_pv_is("CHANNEL:SP.{}ST".format(index_as_name), channel_as_name)
            self.ca.assert_that_pv_is("CHANNEL:SP.{}SV".format(index_as_name), ChannelAccess.ALARM_NONE)

            self.ca.set_pv_value("CHANNEL:SP", index)
            self.ca.assert_pv_alarm_is("CHANNEL:SP", ChannelAccess.ALARM_NONE)

    @skip_if_recsim("In rec sim we can not disconnect the device from the IOC")
    def test_WHEN_the_rig_is_not_connected_THEN_the_status_has_alarm(self):
        self._lewis.backdoor_set_on_device("status", None)

        self.ca.assert_pv_alarm_is("STAT:DISP", ChannelAccess.ALARM_INVALID)

    # Waveform tests

    def check_running_state(self, status, running, continuing, timeout=None):
        self.ca.assert_that_pv_is(wave_prefixed("STATUS"), status, timeout)
        self.ca.assert_that_pv_is(wave_prefixed("RUNNING"), "Running" if running else "Not running", timeout)
        self.ca.assert_that_pv_is(wave_prefixed("CONTINUING"), "Continuing" if continuing else "Not continuing",
                                  timeout)

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_stopped_WHEN_it_is_started_THEN_it_is_running(self):
        self.check_running_state(status="Stopped", running=False, continuing=False)
        self.ca.set_pv_value(wave_prefixed("START"), 1)
        self.check_running_state(status="Running", running=True, continuing=True)

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_stopped_WHEN_it_is_aborted_THEN_it_is_stopped(self):
        self.check_running_state(status="Stopped", running=False, continuing=False)
        self.ca.set_pv_value(wave_prefixed("ABORT"), 1)
        self.check_running_state(status="Stopped", running=False, continuing=False)

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_stopped_WHEN_it_is_stopped_THEN_it_is_stopped(self):
        self.check_running_state(status="Stopped", running=False, continuing=False)
        self.ca.set_pv_value(wave_prefixed("STOP"), 1)
        self.check_running_state(status="Stopped", running=False, continuing=False)

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_running_WHEN_it_is_started_THEN_it_is_running(self):
        self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_RUNNING])
        self.check_running_state(status="Running", running=True, continuing=True)
        self.ca.set_pv_value(wave_prefixed("START"), 1)
        self.check_running_state(status="Running", running=True, continuing=True)

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_running_WHEN_it_is_aborted_THEN_it_is_aborted(self):
        self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_RUNNING])
        self.check_running_state(status="Running", running=True, continuing=True)
        self.ca.set_pv_value(wave_prefixed("ABORT"), 1)
        self.check_running_state(status="Aborted", running=False, continuing=False)

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_running_WHEN_it_is_stopped_THEN_it_is_finishing_and_then_stops_within_5_seconds(self):
        self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_RUNNING])
        self.check_running_state(status="Running", running=True, continuing=True)
        self.ca.set_pv_value(wave_prefixed("STOP"), 1)
        self.check_running_state(status="Finishing", running=True, continuing=False)
        self.check_running_state(status="Stopped", running=False, continuing=False, timeout=5)

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_aborted_WHEN_it_is_started_THEN_it_is_running_and_keeps_running(self):
        self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_ABORTED])
        self.check_running_state(status="Aborted", running=False, continuing=False)
        self.ca.set_pv_value(wave_prefixed("START"), 1)
        self.check_running_state(status="Running", running=True, continuing=True)

        # We need to make sure it can keep running for a few scans. The IOC could feasibly stop the generator shortly
        # after it is started
        time.sleep(5)
        self.check_running_state(status="Running", running=True, continuing=True)

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_aborted_WHEN_it_is_aborted_THEN_it_is_aborted(self):
        self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_ABORTED])
        self.check_running_state(status="Aborted", running=False, continuing=False)
        self.ca.set_pv_value(wave_prefixed("ABORT"), 1)
        self.check_running_state(status="Aborted", running=False, continuing=False)

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_aborted_WHEN_it_is_stopped_THEN_it_is_aborted(self):
        self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_ABORTED])
        self.check_running_state(status="Aborted", running=False, continuing=False)
        self.ca.set_pv_value(wave_prefixed("STOP"), 1)
        self.check_running_state(status="Aborted", running=False, continuing=False)

    def test_WHEN_waveform_type_is_set_THEN_the_device_reports_it_has_changed(self):
        for index, wave_type in enumerate(["Sine", "Triangle", "Square", "Haversine",
                     "Havetriangle", "Haversquare", "Sensor", "Aux", "Sawtooth"]):
            self.ca.assert_setting_setpoint_sets_readback(index, wave_prefixed("TYPE"), expected_value=wave_type)

    @skip_if_recsim("Recsim record does not handle multiple channels ")
    def test_GIVEN_multiple_channels_WHEN_waveform_frequency_is_set_THEN_the_device_is_updated_to_that_value(self):
        expected_values = [123.456, 789.012, 345.678]
        assert len(expected_values) == NUMBER_OF_CHANNELS

        # Do this as two separate loops so that we can verify that all 3 channel values are stored independently
        for device_channel in range(NUMBER_OF_CHANNELS):
            self.ca.set_pv_value("CHANNEL:SP.VAL", device_channel)
            self.ca.set_pv_value(wave_prefixed("FREQ:SP"), expected_values[device_channel])

        for device_channel in range(NUMBER_OF_CHANNELS):
            self.ca.set_pv_value("CHANNEL:SP.VAL", device_channel)
            self.ca.assert_that_pv_is(wave_prefixed("FREQ"), expected_values[device_channel])

    @skip_if_recsim("Conversion factors initialized to 0")
    def test_GIVEN_multiple_channels_WHEN_waveform_amplitude_is_set_THEN_the_device_is_updated_to_that_value_with_channel_conversion_factor_applied(self):
        input_values = [123.4, 567.8, 91.2]
        conversion_factors = [
            float(self.ca.get_pv_value("POS:SCALE"))*1000,
            float(self.ca.get_pv_value("STRESS:SCALE"))/float(self.ca.get_pv_value("STRESS:AREA")),
            float(self.ca.get_pv_value("STRAIN:SCALE"))*100000*float(self.ca.get_pv_value("STRAIN:LENGTH"))
        ]
        expected_values = [input_values[i]/conversion_factors[i] for i in range(NUMBER_OF_CHANNELS)]
        assert len(expected_values) == len(conversion_factors) == len(input_values) == NUMBER_OF_CHANNELS

        # Do this as two separate loops so that we can verify that all 3 channel values are stored independently
        for device_channel in range(NUMBER_OF_CHANNELS):
            self.ca.set_pv_value("CHANNEL:SP.VAL", device_channel)
            self.ca.set_pv_value(wave_prefixed("AMP:SP"), input_values[device_channel])
            self.ca.assert_that_pv_is(wave_prefixed("AMP"), expected_values[device_channel])
            self.ca.assert_that_pv_is(wave_prefixed("AMP:SP:RBV"), input_values[device_channel])

        for device_channel in range(NUMBER_OF_CHANNELS):
            self.ca.set_pv_value("CHANNEL:SP.VAL", device_channel)
            self.ca.assert_that_pv_is(wave_prefixed("AMP"), expected_values[device_channel])
            self.ca.assert_that_pv_is(wave_prefixed("AMP:SP:RBV"), input_values[device_channel])

    @skip_if_recsim("RECSIM does not capture dynamic behaviour")
    def test_WHEN_the_quarter_counter_is_off_THEN_the_number_of_counts_is_and_remains_zero(self):
        self.ca.set_pv_value(quart_prefixed("OFF"), 1)
        self.ca.assert_that_pv_is("QUART", 0)
        self.ca.assert_that_pv_is("QUART", 0, timeout=5)

    @skip_if_recsim("Status more complicated than RECSIM can handle")
    def test_WHEN_the_quarter_counter_is_armed_THEN_the_status_is_armed(self):
        self.ca.set_pv_value(quart_prefixed("ARM"), 1)
        self.ca.assert_that_pv_is(quart_prefixed("STATUS"), "Armed")

    @skip_if_recsim("Counting part of dynamic device behaviour")
    def test_WHEN_the_waveform_generator_is_started_THEN_the_quarter_counter_starts_counting_and_keeps_increasing(self):
        self.ca.set_pv_value(wave_prefixed("START"), 1)
        self.ca.assert_pv_value_is_increasing("QUART", 5)

    @skip_if_recsim("Status more complicated than RECSIM can handle")
    def test_WHEN_the_quarter_counter_is_armed_THEN_the_number_of_quarts_never_exceeds_the_requested_maximum(self):
        cycles = 5
        self.ca.set_pv_value(quart_prefixed("CYCLE:SP"), cycles)
        self.ca.assert_that_pv_is(quart_prefixed("SP"), cycles*4)
        self.ca.set_pv_value(wave_prefixed("START"), 1)
        while self.ca.get_pv_value(quart_prefixed("STATUS")) == "Armed":
            self.assertLessEqual(float(self.ca.get_pv_value("QUART")/4.0), cycles)
        self.ca.assert_that_pv_is(quart_prefixed("STATUS"), "Tripped")

    def test_GIVEN_the_waveform_generator_is_stopped_WHEN_instructed_to_hold_THEN_status_is_stopped(self):
        self.ca.assert_that_pv_is(wave_prefixed("STATUS"), "Stopped")
        self.ca.set_pv_value(wave_prefixed("HOLD"), 1)
        self.ca.assert_that_pv_is(wave_prefixed("STATUS"), "Stopped")

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_running_WHEN_instructed_to_hold_THEN_status_is_holding(self):
        self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_RUNNING])
        self.ca.assert_that_pv_is(wave_prefixed("STATUS"), "Running")
        self.ca.set_pv_value(wave_prefixed("HOLD"), 1)
        self.ca.assert_that_pv_is(wave_prefixed("STATUS"), "Holding")

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_holding_WHEN_instructed_to_hold_THEN_status_is_holding(self):
        self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_HOLDING])
        self.ca.assert_that_pv_is(wave_prefixed("STATUS"), "Holding")
        self.ca.set_pv_value(wave_prefixed("HOLD"), 1)
        self.ca.assert_that_pv_is(wave_prefixed("STATUS"), "Holding")

    @skip_if_recsim("No backdoor in LewisNone")
    def test_GIVEN_the_waveform_generator_is_finishing_WHEN_instructed_to_hold_THEN_status_is_finishing(self):
        self._lewis.backdoor_command(["device", "set_waveform_state", WAVEFORM_FINISHING])
        self.ca.assert_that_pv_is(wave_prefixed("STATUS"), "Finishing")
        self.ca.set_pv_value(wave_prefixed("HOLD"), 1)
        self.ca.assert_that_pv_is(wave_prefixed("STATUS"), "Finishing")

    def verify_channel_abs(self, expected_value):
        self.ca.assert_that_pv_is("POS:RAMP:WFTYP", expected_value)
        self.ca.assert_that_pv_is("STRAIN:RAMP:WFTYP", expected_value)
        self.ca.assert_that_pv_is("STRESS:RAMP:WFTYP", expected_value)

    def test_WHEN_the_waveform_generator_is_started_THEN_every_axis_is_set_to_ramp(self):
        self.ca.set_pv_value(wave_prefixed("START"), 1)
        self.verify_channel_abs(RAMP_WAVEFORM_TYPES[0])

    def test_WHEN_the_waveform_generator_is_stopped_THEN_every_axis_is_set_to_absolute_ramp(self):
        self.ca.set_pv_value(wave_prefixed("STOP"), 1)
        self.verify_channel_abs(RAMP_WAVEFORM_TYPES[3])

    @skip_if_recsim("Different statuses don't interact in RECSIM")
    def test_WHEN_the_waveform_generator_is_started_THEN_the_quarter_counter_is_armed(self):
        self.ca.set_pv_value(wave_prefixed("START"), 1)
        self.ca.assert_that_pv_is(quart_prefixed("STATUS"), "Armed")

    def test_WHEN_the_max_cyles_is_set_THEN_the_readback_matches_setpoint(self):
        value = 7
        self.ca.assert_setting_setpoint_sets_readback(value=value, set_point_pv=quart_prefixed("CYCLE:SP"),
                                                      readback_pv=quart_prefixed("CYCLE:SP:RBV"))
