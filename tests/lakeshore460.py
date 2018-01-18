import unittest
from unittest import skipIf
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc
from utils.ioc_launcher import IOCRegister

vectors = {1: "XYZ", 2: "XY", 3: "XZ", 4: "YZ", 5: "X-Y"}
channels = ["X", "Y", "Z", "V"]
multipliers = {0: "u", 1: "m", 2: " ", 3: "k"}
ranges = {1: "First Range", 2: "Second Range", 3: "Third Range", 4: "Fourth Range"}


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
        self.ca = ChannelAccess(device_prefix="LKSH460_01", default_timeout=30)
        self.ca.wait_for("IDN")

    def test_GIVEN_unit_set_gauss_WHEN_read_THEN_unit_is_gauss(self):
        unit_string = UnitStrings.GAUSS
        unit_flag = UnitFlags.GAUSS
        self.ca.assert_setting_setpoint_sets_readback(unit_flag, "UNIT", "UNIT:SP", unit_string)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_magnetic_field_reading_set_WHEN_read_THEN_magnetic_field_reading_is_set_value(self):
        for chan in channels:
            set_field_reading = 1.2356
            self._lewis.backdoor_command(["device", "set_channel_param", chan, "field_reading", str(set_field_reading)])
            self.ca.assert_that_pv_is("{}:FIELDREADING".format(chan), set_field_reading)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_prms_set_rms_WHEN_read_THEN_prms_is_rms(self):
        for chan in channels:
            set_prms = UnitFlags.PEAK
            expected_prms = UnitStrings.PEAK
            self.ca.assert_setting_setpoint_sets_readback(set_prms, "{}:PRMS".format(chan),
                                                          "{}:PRMS:SP".format(chan), expected_prms)
    
    def test_GIVEN_unit_set_tesla_WHEN_read_THEN_unit_is_tesla(self):
        unit_string = UnitStrings.TESLA
        unit_flag = UnitFlags.TESLA
        self.ca.assert_setting_setpoint_sets_readback(unit_flag, "UNIT", "UNIT:SP", unit_string)
    
    def test_GIVEN_source_set_WHEN_read_THEN_source_is_set_value(self):
        for key in vectors:
            set_value = key
            expected_value = vectors[key]
            self.ca.assert_setting_setpoint_sets_readback(set_value, "SOURCE", "SOURCE:SP", expected_value)
            
    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_max_hold_reading_set_WHEN_read_THEN_max_hold_reading_is_set_value(self):
        for chan in channels:
            set_max_hold_reading = 2.1234
            self._lewis.backdoor_command(
                ["device", "set_channel_param", chan, "max_hold_reading", str(set_max_hold_reading)])
            self.ca.assert_that_pv_is("{}:MAXREADING".format(chan), set_max_hold_reading)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_rel_mode_reading_set_WHEN_read_THEN_rel_mode_reading_is_set_value(self):
        for chan in channels:
            set_rel_reading = 0.9786
            self._lewis.backdoor_command(
                ["device", "set_channel_param", chan, "rel_mode_reading", str(set_rel_reading)])
            self.ca.assert_that_pv_is("{}:RELMODEREADING".format(chan), set_rel_reading)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_output_mode_set_DC_WHEN_read_THEN_output_mode_is_dc(self):
        for chan in channels:
            mode_set = UnitFlags.DC
            expected_mode = UnitStrings.DC
            self.ca.assert_setting_setpoint_sets_readback(mode_set, "{}:MODE".format(chan),
                                                          "{}:MODE:SP".format(chan), expected_mode)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_output_mode_set_AC_WHEN_read_THEN_output_mode_is_ac(self):
        for chan in channels:
            mode_set = UnitFlags.AC
            expected_mode = UnitStrings.AC
            self.ca.assert_setting_setpoint_sets_readback(mode_set, "{}:MODE".format(chan),
                                                          "{}:MODE:SP".format(chan), expected_mode)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_prms_set_peak_WHEN_read_THEN_prms_is_peak(self):
        for chan in channels:
            set_prms = UnitFlags.RMS
            expected_prms = UnitStrings.RMS
            self.ca.assert_setting_setpoint_sets_readback(set_prms, "{}:PRMS".format(chan),
                                                          "{}:PRMS:SP".format(chan), expected_prms)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_display_filter_set_on_WHEN_read_THEN_display_filter_is_set_value(self):
        for chan in channels:
            set_filter = UnitFlags.ON
            expected_filter = UnitStrings.ON
            self.ca.assert_setting_setpoint_sets_readback(set_filter, "{}:FILTER".format(chan),
                                                          "{}:FILTER:SP".format(chan), expected_filter)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_display_filter_set_off_WHEN_read_THEN_display_filter_is_set_value(self):
        for chan in channels:
            set_filter = UnitFlags.OFF
            expected_filter = UnitStrings.OFF
            self.ca.assert_setting_setpoint_sets_readback(set_filter, "{}:FILTER".format(chan),
                                                          "{}:FILTER:SP".format(chan), expected_filter)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_rel_mode_status_set_on_WHEN_read_THEN_rel_mode_status_is_set_value(self):
        for chan in channels:
            set_rel_mode_status = UnitFlags.ON
            expected_rel_mode_status = UnitStrings.ON
            self.ca.assert_setting_setpoint_sets_readback(set_rel_mode_status, "{}:RELMODE".format(chan),
                                                          "{}:RELMODE:SP".format(chan), expected_rel_mode_status)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_rel_mode_status_set_off_WHEN_read_THEN_rel_mode_status_is_set_value(self):
        for chan in channels:
            set_rel_mode_status = UnitFlags.OFF
            expected_rel_mode_status = UnitStrings.OFF
            self.ca.assert_setting_setpoint_sets_readback(set_rel_mode_status, "{}:RELMODE".format(chan),
                                                          "{}:RELMODE:SP".format(chan), expected_rel_mode_status)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_auto_mode_status_set_on_WHEN_read_THEN_auto_mode_status_is_set_value(self):
        for chan in channels:
            set_auto_mode_status = UnitFlags.ON
            expected_auto_mode_status = UnitStrings.ON
            self.ca.assert_setting_setpoint_sets_readback(set_auto_mode_status, "{}:AUTO".format(chan),
                                                          "{}:AUTO:SP".format(chan), expected_auto_mode_status)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_auto_mode_status_set_off_WHEN_read_THEN_auto_mode_status_is_set_value(self):
        for chan in channels:
            set_auto_mode_status = UnitFlags.OFF
            expected_auto_mode_status = UnitStrings.OFF
            self.ca.assert_setting_setpoint_sets_readback(set_auto_mode_status, "{}:AUTO".format(chan),
                                                          "{}:AUTO:SP".format(chan), expected_auto_mode_status)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_max_hold_status_set_on_WHEN_read_THEN_max_hold_status_is_set_value(self):
        for chan in channels:
            set_max_hold_status = UnitFlags.ON
            expected_max_hold_status = UnitStrings.ON
            self.ca.assert_setting_setpoint_sets_readback(set_max_hold_status, "{}:MAXHOLD".format(chan),
                                                          "{}:MAXHOLD:SP".format(chan), expected_max_hold_status)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_max_hold_status_set_off_WHEN_read_THEN_max_hold_status_is_set_value(self):
        for chan in channels:
            set_max_hold_status = UnitFlags.OFF
            expected_max_hold_status = UnitStrings.OFF
            self.ca.assert_setting_setpoint_sets_readback(set_max_hold_status, "{}:MAXHOLD".format(chan),
                                                          "{}:MAXHOLD:SP".format(chan), expected_max_hold_status)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_channel_status_set_on_WHEN_read_THEN_channel_status_is_set_value(self):
        for chan in channels:
            set_channel_status = UnitFlags.ON
            expected_channel_status = UnitStrings.ON
            self.ca.assert_setting_setpoint_sets_readback(set_channel_status, "{}:STATUS".format(chan),
                                                          "{}:STATUS:SP".format(chan), expected_channel_status)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_channel_status_set_off_WHEN_read_THEN_channel_status_is_set_value(self):
        for chan in channels:
            set_channel_status = UnitFlags.OFF
            expected_channel_status = UnitStrings.OFF
            self.ca.assert_setting_setpoint_sets_readback(set_channel_status, "{}:STATUS".format(chan),
                                                          "{}:STATUS:SP".format(chan), expected_channel_status)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_filter_windows_set_WHEN_read_THEN_alarm_is_major(self):
        for chan in channels:
            filter_windows = 11
            self.ca.assert_setting_setpoint_sets_readback(filter_windows, "{}:FWIN".format(chan),
                                                          "{}:FWIN:SP".format(chan), filter_windows,
                                                          expected_alarm="MAJOR")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_filter_windows_set_WHEN_read_THEN_alarm_is_none(self):
        for chan in channels:
            filter_windows = 4
            self.ca.assert_setting_setpoint_sets_readback(filter_windows, "{}:FWIN".format(chan),
                                                          "{}:FWIN:SP".format(chan), filter_windows,
                                                          expected_alarm="NO_ALARM")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_filter_points_set_WHEN_read_THEN_alarm_is_major(self):
        for chan in channels:
            filter_points = 65
            self.ca.assert_setting_setpoint_sets_readback(filter_points, "{}:FNUM".format(chan),
                                                          "{}:FNUM:SP".format(chan), filter_points,
                                                          expected_alarm="MAJOR")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_filter_points_set_WHEN_read_THEN_alarm_is_none(self):
        for chan in channels:
            filter_points = 10
            self.ca.assert_setting_setpoint_sets_readback(filter_points, "{}:FNUM".format(chan),
                                                          "{}:FNUM:SP".format(chan), filter_points,
                                                          expected_alarm="NO_ALARM")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_range_set_WHEN_read_THEN_range_is_set_value(self):
        for chan in channels:
            for key in ranges:
                set_range = key
                expected_range = ranges[key]
                self.ca.assert_setting_setpoint_sets_readback(set_range, "{}:RANGE".format(chan),
                                                              "{}:RANGE:SP".format(chan), expected_range)
