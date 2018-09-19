from hamcrest import assert_that, is_, equal_to
import unittest
import ast

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "KHLY2001_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KHLY2001"),
        "macros": {},
        "emulator": "keithley_2001",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class StartUpTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2001", DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("IDN")

    @skip_if_recsim("Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_buffer_is_cleared_before_starting(self):
        # Given:
        self.ca.process_pv("startup")

        # Then:
        buffer_cleared = self._lewis.backdoor_get_from_device("buffer_cleared")
        assert_that(buffer_cleared, is_(False))

    @skip_if_recsim("Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_with_no_channels_set_to_active_THEN_no_channels_are_set_to_scan(
            self):
        # Given:
        self.ca.process_pv("startup")

        # Then:
        expected_channels = [1]
        channels_to_scan = list(self._lewis.backdoor_get_from_device("channels_to_scan"))
        assert_that(channels_to_scan, is_(equal_to(expected_channels)))

    @skip_if_recsim("Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_with_one_channels_set_to_active_THEN_only_the_active_channels_are_set_to_scan(
            self):
        # Given:
        self.ca.set_pv_value("CHAN:01:ACTIVE", 1)
        self.ca.process_pv("startup")

        # Then:
        expected_channels = [1]
        channels_to_scan = list(self._lewis.backdoor_get_from_device("channels_to_scan"))
        assert_that(channels_to_scan, is_(equal_to(expected_channels)))

    @skip_if_recsim("Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_with_first_four_channels_set_to_active_THEN_only_the_active_channels_are_set_to_scan(
            self):
        # Given:
        expected_channels = [1, 2, 3, 4]

        for i in expected_channels:
            self.ca.set_pv_value("CHAN:0{}:ACTIVE".format(i), 1)
        self.ca.process_pv("startup")

        # Then:
        channels_to_scan = list(self._lewis.backdoor_get_from_device("channels_to_scan"))
        assert_that(channels_to_scan, is_(equal_to(expected_channels)))

    def GIVEN_a_fresh_IOC_THEN_the_initialization_mode_is_set_to_continuous(self):
        # Given:
        self.ca.process_pv("startup")

        # Then:
        initialization_mode = list(self._lewis.backdoor_get_from_device("initialization_mode"))
        assert_that(initialization_mode, is_(equal_to("continuous")))

    @skip_if_recsim("Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_scan_rate_is_set_to_half_a_second(self):
        # Given:
        self.ca.process_pv("startup")

        # Then:
        scan_rate = float(self._lewis.backdoor_get_from_device("scan_rate"))
        assert_that(scan_rate, is_(equal_to(0.5)))

    @skip_if_recsim("Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_measurement_mode_for_each_channel_is_VDC(self):
        # Given:
        self.ca.process_pv("startup")

        # Then:
        expected_measurement_modes = {
            "CHAN:01": "V:DC",
            "CHAN:02": "V:DC",
            "CHAN:03": "V:DC",
            "CHAN:04": "V:DC",
            "CHAN:06": "V:DC",
            "CHAN:07": "V:DC",
            "CHAN:08": "V:DC",
            "CHAN:09": "V:DC"
        }
        measurement_modes = ast.literal_eval(self._lewis.backdoor_get_from_device("scan_rate"))
        assert_that(measurement_modes, is_(equal_to(expected_measurement_modes)))

    def test_WHEN_fres_digits_set_THEN_fres_digits_matches_the_set_state_AND_alarm_is_major(self):
        expected_alarm = "MAJOR"
        sample_data = [3, 8, 10]
        for sample_value in sample_data:
            self.ca.assert_setting_setpoint_sets_readback(sample_value, "FRES:DIGITS", expected_alarm=expected_alarm)

    def test_WHEN_fres_digits_set_THEN_fres_digits_matches_the_set_state_AND_alarm_is_none(self):
        expected_alarm = "NO_ALARM"
        sample_data = [4, 6]
        for sample_value in sample_data:
            self.ca.assert_setting_setpoint_sets_readback(sample_value, "FRES:DIGITS", expected_alarm=expected_alarm)

    def test_WHEN_start_channel_range_set_THEN_start_channel_matches_the_set_state(self):
        sample_channels = [101, 109, 205]
        for channel in sample_channels:
            self.ca.assert_setting_setpoint_sets_readback(channel, "CH:START")

    def test_WHEN_end_channel_range_set_THEN_end_channel_matches_the_set_state(self):
        sample_channels = [201, 209, 210]
        for channel in sample_channels:
            self.ca.assert_setting_setpoint_sets_readback(channel, "CH:END")

    def test_WHEN_measurement_mode_set_THEN_mesaurement_mode_matches_the_set_state(self):
        self.ca.set_pv_value("CH:START:SP", 101)
        self.ca.set_pv_value("CH:END:SP", 210)
        sample_data = {0: "VOLT:DC", 1: "VOLT:AC", 2: "CURR:DC", 3: "CURR:AC", 4: "RES", 5: "FRES", 6: "CONT",
                       7: "FREQ", 8: "PER"}
        for measurement_enum, measurement_string in sample_data.items():
            self.ca.assert_setting_setpoint_sets_readback(measurement_string, "MEASUREMENT",
                                                          expected_value=measurement_string)

    def test_WHEN_elements_set_THEN_elements_are_as_expected(self):
        elements = "READ, CHAN, TST"
        self.ca.assert_setting_setpoint_sets_readback(elements, "DATAELEMENTS")

