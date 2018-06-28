import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


EMULATOR_NAME = "kynctm3k"

DEVICE_PREFIX = "KYNCTM3K_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KYNCTM3K"),
        "emulator": EMULATOR_NAME,
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Kynctm3KTests(unittest.TestCase):
    """
    Tests for the Keyence TM-3001P IOC.
    """

    # Defines the OUT channels which are on/off for each program
    program_modes = {"all_off": ["off"]*16,
                     "all_out_of_range": ["out_of_range"]*16,

                     "first_on_rest_out_of_range": ["on",
                                                    "out_of_range", "out_of_range", "out_of_range", "out_of_range",
                                                    "out_of_range", "out_of_range", "out_of_range", "out_of_range",
                                                    "out_of_range", "out_of_range", "out_of_range", "out_of_range",
                                                    "out_of_range", "out_of_range", "out_of_range"],

                     "first_on_rest_off": ["on",  "off", "off", "off", "off",
                                           "off", "off", "off", "off", "off",
                                           "off", "off", "off", "off", "off",
                                           "off"],

                     "all_on": ["on"]*16,

                     "even_on_odd_out_of_range": ["out_of_range", "on", "out_of_range", "on", "out_of_range", "on",
                                                  "out_of_range", "on", "out_of_range", "on", "out_of_range", "on",
                                                  "out_of_range", "on", "out_of_range", "on"],

                     "even_on_odd_off": ["off", "on", "off", "on", "off", "on",
                                         "off", "on", "off", "on", "off", "on",
                                         "off", "on", "off", "on"]}

    init_OUT_VALUES = ["off"]*16

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        self._lewis.backdoor_set_on_device("OUT_values", self.init_OUT_VALUES)
        self._lewis.backdoor_set_on_device("truncated_output", False)

    def specify_program_for_device(self, program, channel_value_multiplier):
        """
        Generates a 'program' to write to the emulator, with measurement values or False if a channel is off.
        Args:
            program: A 16 element string array denoting whether an OUTput is "on", "out_of_range" or "off"

            channel_value_multiplier: A constant to multiply the channel number by to obtain its emulated value

        Returns:
            expected_values: A 16 element array containing floats, or False if an OUT address is off.
        """
        expected_values = []
        for channel_to_set, channel_status in enumerate(program):

            if channel_status == "on":
                channel_value = channel_value_multiplier*(channel_to_set+1)
            elif channel_status == "out_of_range":
                channel_value = "out_of_range"
            else:
                channel_value = "off"

            expected_values.append(channel_value)

        return expected_values

    @skip_if_recsim("Backdoor behaviour too complex for RECSIM")
    def test_GIVEN_input_program_WHEN_measurement_value_is_requested_THEN_appropriate_number_of_output_values_are_returned(self):
        for program in self.program_modes:
            for multiplier in [2., -2.718, 2.718]:
                expected_values = self.specify_program_for_device(self.program_modes[program], multiplier)
                self._lewis.backdoor_set_on_device("OUT_values", expected_values)

                for channel_to_test, expected_value in enumerate(expected_values):
                    pv = "MEAS:OUT:{:02d}".format(channel_to_test + 1)
                    if expected_value in ("off", "out_of_range"):
                        continue
                    else:
                        self.ca.assert_that_pv_is_number(pv, expected_value, tolerance=0.01*abs(expected_value))
                        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)

    @skip_if_recsim("Backdoor behaviour too complex for RECSIM")
    def test_GIVEN_input_program_WHEN_all_OUT_values_are_out_of_range_THEN_disconnected_is_shown_for_all(self):
        expected_values = self.specify_program_for_device(self.program_modes['all_out_of_range'], 1.)

        self._lewis.backdoor_set_on_device("OUT_values", expected_values)

        for channel in range(1, 17):
            pv = "MEAS:OUT:{:02d}".format(channel)
            self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.MAJOR)

    @skip_if_recsim("Backdoor behaviour too complex for RECSIM")
    def test_GIVEN_input_program_WHEN_some_measurement_values_are_out_of_range_THEN_appropriate_number_of_output_values_are_returned(self):
        for program in self.program_modes:
            for multiplier in [2., -2.718, 2.718]:
                expected_values = self.specify_program_for_device(self.program_modes[program], multiplier)
                self._lewis.backdoor_set_on_device("OUT_values", expected_values)

                for channel_to_test, expected_value in enumerate(expected_values):
                    pv = "MEAS:OUT:{:02d}".format(channel_to_test + 1)
                    if expected_value == "out_of_range":
                        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.MAJOR)
                    elif type(expected_value) is float:
                        self.ca.assert_that_pv_is_number(pv, expected_value, tolerance=0.01*abs(expected_value))
                        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)
                    else:
                        pass

    def test_GIVEN_input_program_WHEN_all_OUT_measurements_turned_off_THEN_all_pv_alarms_are_raised(self):
        expected_values = self.specify_program_for_device(self.program_modes["all_off"], 1.)

        self._lewis.backdoor_set_on_device("OUT_values", expected_values)

        for channel in range(1, 17):
            pv = "MEAS:OUT:{:02d}".format(channel)
            self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.INVALID)

    @skip_if_recsim("Backdoor behaviour too complex for RECSIM")
    def test_GIVEN_input_program_WHEN_some_OUT_measurements_are_turned_off_THEN_those_pv_alarms_are_raised(self):
        for program in ["first_on_rest_off", "even_on_odd_off"]:
            expected_values = self.specify_program_for_device(self.program_modes[program], 1.)

            self._lewis.backdoor_set_on_device("OUT_values", expected_values)

            for channel_to_test, expected_value in enumerate(expected_values):
                pv = "MEAS:OUT:{:02d}".format(channel_to_test + 1)
                if expected_value == "off":
                    self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.INVALID)
                elif type(expected_value) is float:
                    self.ca.assert_that_pv_is_number(pv, expected_value, tolerance=0.01 * abs(expected_value))
                    self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)
                else:
                    pass

    @skip_if_recsim("Backdoor behaviour too complex for RECSIM")
    def test_GIVEN_a_truncated_output_string_THEN_all_pv_alarms_are_raised(self):
        expected_values = self.specify_program_for_device(self.program_modes["all_on"], 2.)

        self._lewis.backdoor_set_on_device("truncated_output", True)

        self._lewis.backdoor_set_on_device("OUT_values", expected_values)

        for channel in range(1, 17):
            pv = "MEAS:OUT:{:02d}".format(channel)
            self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.INVALID)

    def test_GIVEN_emulator_is_in_auto_send_state_THEN_auto_send_is_unset_and_pvs_read_normally(self):
        expected_values = self.specify_program_for_device(self.program_modes["all_on"], 2.)

        self._lewis.backdoor_set_on_device("auto_send", True)

        for channel_to_test, expected_value in enumerate(expected_values):
            pv = "MEAS:OUT:{:02d}".format(channel_to_test + 1)

            self.ca.assert_that_pv_is_number(pv, expected_value, tolerance=0.01 * abs(expected_value))
