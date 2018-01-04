import unittest
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc

vector_dict = {1: "XYZ", 2: "XY", 3: "XZ", 4: "YZ", 5: "X-Y"}
channels_array = ["X", "Y", "Z", "V"]
multipliers_dict = {0: "u", 1: "m", 2: " ", 3: "k"}
range_dict = {1: "First Range", 2: "Second Range", 3: "Third Range", 4: "Fourth Range"}


class UnitStrings(object):
    GAUSS = "G"
    TESLA = "T"
    ON = "ON"
    OFF = "OFF"
    AC = "AC"
    DC = "DC"
    PEAK = "PEAK"
    RMS = "RMS"


class UnitFlags(object):
    GAUSS = 0
    TESLA = 1
    OFF = 0
    ON = 1
    AC = 1
    DC = 0
    PEAK = 1
    RMS = 0


class Lakeshore460Tests(unittest.TestCase):
    """
    Tests for the Lakeshore460.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("lakeshore460")
        self.ca = ChannelAccess(default_timeout=30)
        self.ca.wait_for("LKSH460_01:IDN")

    def test_GIVEN_unit_set_gauss_WHEN_read_THEN_unit_is_as_expected(self):
        unit_string = UnitStrings.GAUSS
        unit_flag = UnitFlags.GAUSS
        self.ca.set_pv_value("LKSH460_01:UNIT:SP", unit_flag)
        self.ca.assert_that_pv_is("LKSH460_01:UNIT", unit_string)

    def test_GIVEN_unit_set_tesla_WHEN_read_THEN_unit_is_as_expected(self):
        unit_string = UnitStrings.TESLA
        unit_flag = UnitFlags.TESLA
        self.ca.set_pv_value("LKSH460_01:UNIT:SP", unit_flag)
        self.ca.assert_that_pv_is("LKSH460_01:UNIT", unit_string)

    def test_GIVEN_source_set_WHEN_read_THEN_source_is_as_expected(self):
        for key in vector_dict:
            set_value = key
            expected_value = vector_dict[key]
            self.ca.set_pv_value("LKSH460_01:SOURCE:SP", set_value)
            self.ca.assert_that_pv_is("LKSH460_01:SOURCE", expected_value)
            
    def test_GIVEN_magnetic_field_reading_set_WHEN_read_THEN_magnetic_field_reading_is_as_expected(self):
        for chan in channels_array:
            set_field_reading = 1.11
            self._lewis.backdoor_command(["device", "set_channel_param", chan, "field_reading", str(set_field_reading)])
            self.ca.assert_that_pv_is("LKSH460_01:{}:FIELDREADING".format(chan), set_field_reading)

    def test_GIVEN_max_hold_reading_set_WHEN_read_THEN_max_hold_reading_is_as_expected(self):
        for chan in channels_array:
            set_max_hold_reading = 2.1234
            self._lewis.backdoor_command(["device", "set_channel_param", chan, "max_hold_reading", str(set_max_hold_reading)])
            self.ca.assert_that_pv_is("LKSH460_01:{}:MAXREADING".format(chan), set_max_hold_reading)

    def test_GIVEN_rel_mode_reading_set_WHEN_read_THEN_rel_mode_reading_is_as_expected(self):
        for chan in channels_array:
            set_rel_reading = 0.9786
            self._lewis.backdoor_command(["device", "set_channel_param", chan, "rel_mode_reading", str(set_rel_reading)])
            self.ca.assert_that_pv_is("LKSH460_01:{}:RELMODEREADING".format(chan), set_rel_reading)
            
    def test_GIVEN_output_mode_set_DC_WHEN_read_THEN_output_mode_is_as_expected(self):
        for chan in channels_array:
            mode_set = UnitFlags.DC
            expected_mode = UnitStrings.DC
            self.ca.set_pv_value("LKSH460_01:{}:MODE:SP".format(chan), mode_set)
            self.ca.assert_that_pv_is("LKSH460_01:{}:MODE".format(chan), expected_mode)

    def test_GIVEN_output_mode_set_AC_WHEN_read_THEN_output_mode_is_as_expected(self):
        for chan in channels_array:
            mode_set = UnitFlags.AC
            expected_mode = UnitStrings.AC
            self.ca.set_pv_value("LKSH460_01:{}:MODE:SP".format(chan), mode_set)
            self.ca.assert_that_pv_is("LKSH460_01:{}:MODE:SP".format(chan), expected_mode)

    def test_GIVEN_prms_set_rms_WHEN_read_THEN_prms_is_as_expected(self):
        for chan in channels_array:
            set_prms = UnitFlags.PEAK
            expected_prms = UnitStrings.PEAK
            self.ca.set_pv_value("LKSH460_01:{}:PRMS:SP".format(chan), set_prms)
            self.ca.assert_that_pv_is("LKSH460_01:{}:PRMS".format(chan), expected_prms)

    def test_GIVEN_prms_set_peak_WHEN_read_THEN_prms_is_as_expected(self):
        for chan in channels_array:
            set_prms = UnitFlags.RMS
            expected_prms = UnitStrings.RMS
            self.ca.set_pv_value("LKSH460_01:{}:PRMS:SP".format(chan), set_prms)
            self.ca.assert_that_pv_is("LKSH460_01:{}:PRMS".format(chan), expected_prms)
            
    def test_GIVEN_display_filter_set_on_WHEN_read_THEN_display_filter_is_as_expected(self):
        for chan in channels_array:
            set_filter_status = UnitFlags.ON
            expected_filter_status = UnitStrings.ON
            self.ca.set_pv_value("LKSH460_01:{}:FILTER:SP".format(chan), set_filter_status)
            self.ca.assert_that_pv_is("LKSH460_01:{}:FILTER".format(chan), expected_filter_status)
            
    def test_GIVEN_display_filter_set_off_WHEN_read_THEN_display_filter_is_as_expected(self):
        for chan in channels_array:
            set_filter_status = UnitFlags.OFF
            expected_filter_status = UnitStrings.OFF
            self.ca.set_pv_value("LKSH460_01:{}:FILTER:SP".format(chan), set_filter_status)
            self.ca.assert_that_pv_is("LKSH460_01:{}:FILTER".format(chan), expected_filter_status)
            
    def test_GIVEN_rel_mode_status_set_on_WHEN_read_THEN_rel_mode_status_is_as_expected(self):
        for chan in channels_array:
            set_rel_mode_status = UnitFlags.ON
            expected_rel_mode_status = UnitStrings.ON
            self.ca.set_pv_value("LKSH460_01:{}:RELMODE:SP".format(chan), set_rel_mode_status)
            self.ca.assert_that_pv_is("LKSH460_01:{}:RELMODE".format(chan), expected_rel_mode_status)

    def test_GIVEN_rel_mode_status_set_off_WHEN_read_THEN_rel_mode_status_is_as_expected(self):
        for chan in channels_array:
            set_rel_mode_status = UnitFlags.OFF
            expected_rel_mode_status = UnitStrings.OFF
            self.ca.set_pv_value("LKSH460_01:{}:RELMODE:SP".format(chan), set_rel_mode_status)
            self.ca.assert_that_pv_is("LKSH460_01:{}:RELMODE".format(chan), expected_rel_mode_status)
            
    def test_GIVEN_auto_mode_status_set_on_WHEN_read_THEN_auto_mode_status_is_as_expected(self):
        for chan in channels_array:
            set_auto_mode_status = UnitFlags.ON
            expected_auto_mode_status = UnitStrings.ON
            self.ca.set_pv_value("LKSH460_01:{}:AUTO:SP".format(chan), set_auto_mode_status)
            self.ca.assert_that_pv_is("LKSH460_01:{}:AUTO".format(chan), expected_auto_mode_status)

    def test_GIVEN_auto_mode_status_set_off_WHEN_read_THEN_auto_mode_status_is_as_expected(self):
        for chan in channels_array:
            set_auto_mode_status = UnitFlags.OFF
            expected_auto_mode_status = UnitStrings.OFF
            self.ca.set_pv_value("LKSH460_01:{}:AUTO:SP".format(chan), set_auto_mode_status)
            self.ca.assert_that_pv_is("LKSH460_01:{}:AUTO".format(chan), expected_auto_mode_status)
            
    def test_GIVEN_max_hold_status_set_on_WHEN_read_THEN_max_hold_status_is_as_expected(self):
        for chan in channels_array:
            set_max_hold_status = UnitFlags.ON
            expected_max_hold_status = UnitStrings.ON
            self.ca.set_pv_value("LKSH460_01:{}:MAXHOLD:SP".format(chan), set_max_hold_status)
            self.ca.assert_that_pv_is("LKSH460_01:{}:MAXHOLD".format(chan), expected_max_hold_status)

    def test_GIVEN_max_hold_status_set_off_WHEN_read_THEN_max_hold_status_is_as_expected(self):
        for chan in channels_array:
            set_max_hold_status = UnitFlags.OFF
            expected_max_hold_status = UnitStrings.OFF
            self.ca.set_pv_value("LKSH460_01:{}:MAXHOLD:SP".format(chan), set_max_hold_status)
            self.ca.assert_that_pv_is("LKSH460_01:{}:MAXHOLD".format(chan), expected_max_hold_status)    
                
    def test_GIVEN_channel_status_set_on_WHEN_read_THEN_channel_status_is_as_expected(self):
        for chan in channels_array:
            set_channel_status = UnitFlags.ON
            expected_channel_status = UnitStrings.ON
            self.ca.set_pv_value("LKSH460_01:{}:STATUS:SP".format(chan), set_channel_status)
            self.ca.assert_that_pv_is("LKSH460_01:{}:STATUS".format(chan), expected_channel_status)

    def test_GIVEN_channel_status_set_off_WHEN_read_THEN_channel_status_is_as_expected(self):
        for chan in channels_array:
            set_channel_status = UnitFlags.OFF
            expected_channel_status = UnitStrings.OFF
            self.ca.set_pv_value("LKSH460_01:{}:STATUS:SP".format(chan), set_channel_status)
            self.ca.assert_that_pv_is("LKSH460_01:{}:STATUS".format(chan), expected_channel_status)
            
    def test_GIVEN_filter_windows_set_WHEN_read_THEN_alarm_is_major(self):
        for chan in channels_array:
            filter_windows = 11
            self.ca.set_pv_value("LKSH460_01:{}:FWIN:SP".format(chan), filter_windows)
            self.ca.assert_pv_alarm_is("LKSH460_01:{}:FWIN".format(chan), self.ca.ALARM_MAJOR)
            self.ca.assert_that_pv_is("LKSH460_01:{}:FWIN".format(chan), filter_windows)

    def test_GIVEN_filter_windows_set_WHEN_read_THEN_alarm_is_none(self):
        for chan in channels_array:
            filter_windows = 4
            self.ca.set_pv_value("LKSH460_01:{}:FWIN:SP".format(chan), filter_windows)
            self.ca.assert_pv_alarm_is("LKSH460_01:{}:FWIN".format(chan), self.ca.ALARM_NONE)
            self.ca.assert_that_pv_is("LKSH460_01:{}:FWIN".format(chan), filter_windows) 

    def test_GIVEN_filter_points_set_WHEN_read_THEN_alarm_is_major(self):
        for chan in channels_array:
            filter_points = 65
            self.ca.set_pv_value("LKSH460_01:{}:FNUM:SP".format(chan), filter_points)
            self.ca.assert_pv_alarm_is("LKSH460_01:{}:FNUM".format(chan), self.ca.ALARM_MAJOR)
            self.ca.assert_that_pv_is("LKSH460_01:{}:FNUM".format(chan), filter_points)

    def test_GIVEN_filter_points_set_WHEN_read_THEN_alarm_is_none(self):
        for chan in channels_array:
            filter_points = 10
            self.ca.set_pv_value("LKSH460_01:{}:FNUM:SP".format(chan), filter_points)
            self.ca.assert_pv_alarm_is("LKSH460_01:{}:FNUM".format(chan), self.ca.ALARM_NONE)
            self.ca.assert_that_pv_is("LKSH460_01:{}:FNUM".format(chan), filter_points)     
                
    def test_GIVEN_range_set_WHEN_read_THEN_range_is_as_expected(self):
        for chan in channels_array:
            for key in range_dict:
                set_range = key
                expected_range = range_dict[key]
                self.ca.set_pv_value("LKSH460_01:{}:RANGE:SP".format(chan), set_range)
                self.ca.assert_that_pv_is("LKSH460_01:{}:RANGE".format(chan), expected_range)
    