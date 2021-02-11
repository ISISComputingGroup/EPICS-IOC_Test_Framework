import unittest
from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list
from utils.ioc_launcher import get_default_ioc_dir

vectors = {1: "XYZ", 2: "XY", 3: "XZ", 4: "YZ", 5: "X-Y"}
channels = ["X", "Y", "Z", "V"]
multipliers = {0: "u", 1: "m", 2: " ", 3: "k"}
ranges = {1: "First Range", 2: "Second Range", 3: "Third Range", 4: "Fourth Range"}


DEVICE_PREFIX = "LKSH460_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LKSH460"),
        "macros": {},
        "emulator": "lakeshore460"
    },
]

TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


class UnitStrings(object):
    GAUSS = "G"
    TESLA = "T"
    ON = "ON"
    OFF = "OFF"
    AC = "AC"
    DC = "DC"
    PEAK = "PEAK"
    RMS = "RMS"
    CHANNEL_ON = "ON"
    CHANNEL_OFF = "OFF"


class UnitFlags(object):
    GAUSS = 0
    TESLA = 1
    OFF = 0
    ON = 1
    AC = 1
    DC = 0
    PEAK = 1
    RMS = 0
    CHANNEL_OFF = 1
    CHANNEL_ON = 0


class Lakeshore460Tests(unittest.TestCase):
    """
    Tests for the Lakeshore460.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("lakeshore460", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix="LKSH460_01", default_timeout=30, default_wait_time=0.0)
        self.ca.assert_that_pv_exists("IDN")

    @parameterized.expand([("tesla", UnitFlags.TESLA, UnitStrings.TESLA),
                           ("gauss", UnitFlags.GAUSS, UnitStrings.GAUSS)])
    def test_GIVEN_unit_set_to_value_WHEN_read_THEN_unit_is_value(self, _, unit_flag, unit_string):
        self.ca.set_pv_value("CHANNEL", "X")
        self.ca.assert_setting_setpoint_sets_readback(unit_flag, "UNIT", expected_value=unit_string)

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_magnetic_field_reading_set_WHEN_read_THEN_magnetic_field_reading_is_set_value(self):
        for chan in channels:
            set_field_reading = 1.2356
            self._lewis.backdoor_command(["device", "set_channel_param", chan, "field_reading", str(set_field_reading)])
            self.ca.assert_that_pv_is("{}:FIELD:RAW".format(chan), set_field_reading)

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_prms_set_peak_WHEN_read_THEN_prms_is_peak(self):
        for chan in channels:
            set_prms = UnitFlags.PEAK
            expected_prms = UnitStrings.PEAK
            self.ca.assert_setting_setpoint_sets_readback(set_prms, "{}:PRMS".format(chan),
                                                          expected_value=expected_prms, timeout=15)

    def test_GIVEN_source_set_WHEN_read_THEN_source_is_set_value(self):
        for key in vectors:
            set_value = key
            expected_value = vectors[key]
            self.ca.assert_setting_setpoint_sets_readback(set_value, "SOURCE", expected_value=expected_value)

    @parameterized.expand([("DC", UnitFlags.DC, UnitStrings.DC),
                           ("AC", UnitFlags.AC, UnitStrings.AC)])
    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_output_mode_set_to_value_WHEN_read_THEN_output_mode_is_value(self, _, unit_flag, unit_string):
        for chan in channels:
            self.ca.assert_setting_setpoint_sets_readback(unit_flag, "{}:MODE".format(chan),
                                                          expected_value=unit_string)

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_prms_set_rms_WHEN_read_THEN_prms_is_rms(self):
        for chan in channels:
            set_prms = UnitFlags.RMS
            expected_prms = UnitStrings.RMS
            self.ca.assert_setting_setpoint_sets_readback(set_prms, "{}:PRMS".format(chan),
                                                          expected_value=expected_prms, timeout=15)

    @parameterized.expand([("ON", UnitFlags.ON, UnitStrings.ON),
                           ("OFF", UnitFlags.OFF, UnitStrings.OFF)])
    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_display_filter_set_to_val_WHEN_read_THEN_display_filter_is_set_value(self, _, unit_flag, unit_string):
        for chan in channels:
            self.ca.assert_setting_setpoint_sets_readback(unit_flag, "{}:FILTER".format(chan),
                                                          expected_value=unit_string)

    @parameterized.expand([("ON", UnitFlags.ON, UnitStrings.ON),
                           ("OFF", UnitFlags.OFF, UnitStrings.OFF)])
    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_rel_mode_status_set_to_val_WHEN_read_THEN_rel_mode_status_is_set_value(self, _, unit_flag, unit_string):
        for chan in channels:
            self.ca.assert_setting_setpoint_sets_readback(unit_flag, "{}:RELMODE".format(chan),
                                                          expected_value=unit_string)

    @parameterized.expand(parameterized_list([10.4, 20, 3]))
    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_rel_mode_setpoint_set_to_val_WHEN_read_THEN_rel_mode_setpoint_is_set_value(self, _, value):
        for chan in channels:
            self.ca.assert_setting_setpoint_sets_readback(value, "{}:RELMODESET".format(chan))

    @parameterized.expand([("ON", UnitFlags.ON, UnitStrings.ON),
                           ("OFF", UnitFlags.OFF, UnitStrings.OFF)])
    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_auto_mode_status_set_to_value_WHEN_read_THEN_auto_mode_status_is_set_value(self, _, unit_flag, unit_string):
        for chan in channels:
            self.ca.assert_setting_setpoint_sets_readback(unit_flag, "{}:AUTO".format(chan),
                                                          expected_value=unit_string)

    @parameterized.expand([("ON", UnitFlags.ON, UnitStrings.ON),
                           ("OFF", UnitFlags.OFF, UnitStrings.OFF)])
    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_max_hold_status_set_to_value_WHEN_read_THEN_max_hold_status_is_set_value(self, _, unit_flag, unit_string):
        for chan in channels:
            self.ca.assert_setting_setpoint_sets_readback(unit_flag, "{}:MAXHOLD".format(chan),
                                                          expected_value=unit_string)

    @parameterized.expand([("ON", UnitFlags.CHANNEL_ON, UnitStrings.CHANNEL_ON),
                           ("OFF", UnitFlags.CHANNEL_OFF, UnitStrings.CHANNEL_OFF)])
    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_channel_status_set_on_WHEN_read_THEN_channel_status_is_set_value(self, _, unit_flag, unit_string):
        for chan in channels:
            self.ca.assert_setting_setpoint_sets_readback(unit_flag, "{}:STATUS".format(chan),
                                                          expected_value=unit_string)

    @parameterized.expand([("11_alarm_major", 11, "MAJOR"),
                           ("4_no_alarm", 4, "NO_ALARM")])
    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_filter_windows_set_WHEN_read_THEN_alarm_is_as_expected(self, _, filter_windows, exp_alarm):
        for chan in channels:
            self.ca.assert_setting_setpoint_sets_readback(filter_windows, "{}:FWIN".format(chan),
                                                          expected_alarm=exp_alarm)

    @parameterized.expand([("65_alarm_major", 65, "MAJOR"),
                           ("10_no_alarm", 10, "NO_ALARM")])
    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_filter_points_set_WHEN_read_THEN_alarm_is_major(self, _, filter_points, exp_alarm):
        for chan in channels:
            self.ca.assert_setting_setpoint_sets_readback(filter_points, "{}:FNUM".format(chan),
                                                          expected_alarm=exp_alarm)

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_range_set_WHEN_read_THEN_range_is_set_value(self):
        for chan in channels:
            for key in ranges:
                set_range = key
                expected_range = ranges[key]
                self.ca.assert_setting_setpoint_sets_readback(set_range, "{}:RANGE".format(chan),
                                                              expected_value=expected_range)
