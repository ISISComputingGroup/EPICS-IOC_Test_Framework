import unittest
from unittest import skipIf
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc
from utils.ioc_launcher import IOCRegister


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
    ON = 1
    OFF = 0
    AC = 0
    DC = 1
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

    def _set_IDN(self, expected_idn):
        self._lewis.backdoor_set_on_device("idn", expected_idn)
        self._ioc.set_simulated_value("LKSH460_01:SIM:IDN", expected_idn)

    def _set_max_reading(self, expected_max_reading):
        self._lewis.backdoor_set_on_device("max_reading", expected_max_reading)
        channels = ["X", "Y", "Z", "V"]
        for channel in channels:
            self._ioc.set_simulated_value("LKSH460_01:{0}:SIM:MAXREADING".format(channel), expected_max_reading)

    def _set_unit(self, expected_gauss, expected_tesla):
        expected_channels = {"X": expected_gauss, "Y": expected_tesla, "Z": expected_gauss, "V": expected_tesla}
        for channel, unit in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:UNIT:SP".format(channel), unit)

    def _set_output_status(self, expected_on, expected_off):
        expected_channels = {"X": expected_on, "Y": expected_off, "Z": expected_on, "V": expected_off}
        for channel, unit in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:OUTPUTSTATUS:SP".format(channel), unit)

    def _set_prms(self, expected_peak, expected_rms):
        expected_channels = {"X": expected_peak, "Y": expected_rms, "Z": expected_peak, "V": expected_rms}
        for channel, unit in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:PRMS:SP".format(channel), unit)

    def _set_output_mode(self, expected_ac, expected_dc):
        expected_channels = {"X": expected_ac, "Y": expected_dc, "Z": expected_ac, "V": expected_dc}
        for channel, unit in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:OUTPUTMODE:SP".format(channel), unit)

    def _set_rel_mode_reading(self, expected_rel_mode_reading):
        self._lewis.backdoor_set_on_device("rel_mode_reading", expected_rel_mode_reading)
        channels = ["X", "Y", "Z", "V"]
        for channel in channels:
            self._ioc.set_simulated_value("LKSH460_01:{0}:SIM:RELMODEREADING".format(channel),
                                          expected_rel_mode_reading)

    def _set_magnetic_field_reading(self, expected_magnetic_field_reading):
        self._lewis.backdoor_set_on_device("magnetic_field_reading", expected_magnetic_field_reading)
        channels = ["X", "Y", "Z", "V"]
        for channel in channels:
            self._ioc.set_simulated_value("LKSH460_01:{0}:SIM:FIELDREADING".format(channel), expected_magnetic_field_reading)

    def test_GIVEN_idn_set_WHEN_read_THEN_idn_is_as_expected(self):
        expected_idn = "000000000000000000111111111111111111151"
        self._set_IDN(expected_idn)
        self.ca.set_pv_value("LKSH460_01:IDN.PROC", 1)
        self.ca.assert_that_pv_is("LKSH460_01:IDN", expected_idn)

    def test_GIVEN_unit_set_for_a_channel_WHEN_read_THEN_unit_is_as_expected_for_channel(self):
        expected_unit_tesla_flag = UnitFlags.TESLA
        expected_unit_gauss_flag = UnitFlags.GAUSS
        self._set_unit(expected_unit_gauss_flag, expected_unit_tesla_flag)
        expected_channels = {"X": UnitStrings.GAUSS, "Y": UnitStrings.TESLA, "Z": UnitStrings.GAUSS,
                             "V": UnitStrings.TESLA}
        for channel, unit in expected_channels.iteritems():
            self.ca.assert_that_pv_is("LKSH460_01:{0}:UNIT".format(channel), unit)

    def test_GIVEN_output_status_set_for_a_channel_WHEN_read_THEN_output_STATUS_is_as_expected_for_channel(self):
        expected_on_flag = UnitFlags.ON
        expected_off_flag = UnitFlags.OFF
        self._set_output_status(expected_on_flag, expected_off_flag)
        expected_channels = {"X": UnitStrings.ON, "Y": UnitStrings.OFF,
                             "Z": UnitStrings.ON, "V": UnitStrings.OFF}
        for channel, output_status in expected_channels.iteritems():
            self.ca.assert_that_pv_is("LKSH460_01:{0}:OUTPUTSTATUS".format(channel), output_status)

    def test_GIVEN_output_mode_set_for_a_channel_WHEN_read_THEN_output_mode_is_as_expected_for_channel(self):
        expected_dc_mode_flag = UnitFlags.DC
        expected_ac_mode_flag = UnitFlags.AC
        self._set_output_mode(expected_ac_mode_flag, expected_dc_mode_flag)
        expected_channels = {"X": UnitStrings.AC, "Y": UnitStrings.DC,
                             "Z": UnitStrings.AC, "V": UnitStrings.DC}
        for channel, output_mode in expected_channels.iteritems():
            self.ca.assert_that_pv_is("LKSH460_01:{0}:OUTPUTMODE".format(channel), output_mode)

    def test_GIVEN_prms_set_for_a_channel_WHEN_read_THEN_prms_is_as_expected_for_set_channel(self):
        expected_peak_status_flag = UnitFlags.PEAK
        expected_rms_status_flag = UnitFlags.RMS
        self._set_prms(expected_peak_status_flag, expected_rms_status_flag)
        expected_channels = {"X": UnitStrings.PEAK, "Y": UnitStrings.RMS,
                             "Z": UnitStrings.PEAK, "V": UnitStrings.RMS}
        for channel, prms_status in expected_channels.iteritems():
            self.ca.assert_that_pv_is("LKSH460_01:{0}:PRMS".format(channel), prms_status)

    def test_GIVEN_display_filter_set_for_channel_WHEN_read_THEN_display_filter_is_as_expected_for_channel(self):
        channels = ["X", "Y", "Z", "V"]
        test_data = {UnitFlags.ON: UnitStrings.ON, UnitFlags.OFF: UnitStrings.OFF}
        for channel in channels:
            for input, output in test_data.iteritems():
                self.ca.set_pv_value("LKSH460_01:{0}:FILTER:SP".format(channel), input)
                self.ca.assert_that_pv_is("LKSH460_01:{0}:FILTER".format(channel), output)

    def test_GIVEN_relative_mode_set_for_channel_WHEN_read_THEN_relative_mode_is_as_expected_for_set_channel(self):
        channels = ["X", "Y", "Z", "V"]
        test_data = {UnitFlags.ON: UnitStrings.ON, UnitFlags.OFF: UnitStrings.OFF}
        for channel in channels:
            for input, output in test_data.iteritems():
                self.ca.set_pv_value("LKSH460_01:{0}:RELMODE:SP".format(channel), input)
                self.ca.assert_that_pv_is("LKSH460_01:{0}:RELMODE".format(channel), output)

    def test_GIVEN_max_hold_set_WHEN_read_THEN_max_hold_is_as_expected(self):
        channels = ["X", "Y", "Z", "V"]
        test_data = {UnitFlags.ON: UnitStrings.ON, UnitFlags.OFF: UnitStrings.OFF}
        for channel in channels:
            for input, output in test_data.iteritems():
                self.ca.set_pv_value("LKSH460_01:{0}:MAXHOLD:SP".format(channel), input)
                self.ca.assert_that_pv_is("LKSH460_01:{0}:MAXHOLD".format(channel), output)

    def test_GIVEN_auto_range_set_WHEN_read_THEN_auto_range_is_as_expected(self):
        channels = ["X", "Y", "Z", "V"]
        test_data = {UnitFlags.ON: UnitStrings.ON, UnitFlags.OFF: UnitStrings.OFF}

        for channel in channels:
            for input, output in test_data.iteritems():
                self.ca.set_pv_value("LKSH460_01:{0}:AUTO:SP".format(channel), input)
                self.ca.assert_that_pv_is("LKSH460_01:{0}:AUTO".format(channel), output)

    def test_GIVEN_source_set_WHEN_read_THEN_source_is_as_expected(self):
        expected_source = 2
        self.ca.set_pv_value("LKSH460_01:SOURCE:SP", expected_source)
        self.ca.assert_that_pv_is("LKSH460_01:SOURCE", "XZ")

    def test_GIVEN_filter_window_set_WHEN_read_THEN_filter_window_is_as_expected_AND_within_range(self):
        channels = ["X", "Y", "Z", "V"]
        sample_data = {1: ChannelAccess.ALARM_NONE, 11: ChannelAccess.ALARM_MAJOR,
                       10: ChannelAccess.ALARM_NONE, 22: ChannelAccess.ALARM_MAJOR}
        for channel in channels:
            for percentage, alarm_state in sample_data.iteritems():
                self.ca.set_pv_value("LKSH460_01:{0}:FWIN:SP".format(channel), percentage)
                self.ca.assert_that_pv_is("LKSH460_01:{0}:FWIN".format(channel), percentage)
                self.ca.assert_pv_alarm_is("LKSH460_01:{0}:FWIN".format(channel), alarm_state)

    def test_GIVEN_filter_points_set_WHEN_read_THEN_filter_points_is_as_expected_AND_within_range(self):
        channels = ["X", "Y", "Z", "V"]
        sample_data = {70: ChannelAccess.ALARM_MAJOR, 64: ChannelAccess.ALARM_NONE, 65: ChannelAccess.ALARM_MAJOR,
                       2: ChannelAccess.ALARM_NONE}
        for channel in channels:
            for points, alarm_state in sample_data.iteritems():
                self.ca.set_pv_value("LKSH460_01:{0}:FNUM:SP".format(channel), points)
                self.ca.assert_that_pv_is("LKSH460_01:{0}:FNUM".format(channel), points)
                self.ca.assert_pv_alarm_is("LKSH460_01:{0}:FNUM".format(channel), alarm_state)

    def test_GIVEN_range_set_manually_WHEN_read_THEN_range_is_as_expected(self):
        channels = ["X", "Y", "Z", "V"]
        sample_data = {0: "First Range", 1: "Second Range", 2: "Third Range",
                       3: "Fourth Range"}

        for channel in channels:
            for input, range in sample_data.iteritems():
                self.ca.set_pv_value("LKSH460_01:{0}:RANGE:SP".format(channel), input)
                self.ca.assert_that_pv_is("LKSH460_01:{0}:RANGE".format(channel), range)

    def test_GIVEN_max_reading_set_WHEN_read_THEN_max_reading_is_as_expected(self):
        expected_max_reading = 500
        self._set_max_reading(expected_max_reading)
        self.ca.assert_that_pv_is("LKSH460_01:X:MAXREADING", expected_max_reading)
        self.ca.assert_that_pv_is("LKSH460_01:Y:MAXREADING", expected_max_reading)
        self.ca.assert_that_pv_is("LKSH460_01:Z:MAXREADING", expected_max_reading)
        self.ca.assert_that_pv_is("LKSH460_01:V:MAXREADING", expected_max_reading)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_max_reading_unit_set_WHEN_read_THEN_max_reading_unit_is_as_expected(self):
        channels = ["X", "Y", "Z", "V"]
        sample_data = {0: "uG", 1: "mG", 2: "G", 3: "kG"}

        for channel in channels:
            for input, egu in sample_data.iteritems():
                self.ca.set_pv_value("LKSH460_01:{0}:MAX:MULTIPLIER".format(channel), input)
                self.ca.assert_that_pv_is("LKSH460_01:{0}:MAXREADING.EGU".format(channel), egu)

    def test_GIVEN_relative_mode_set_point_set_WHEN_read_THEN_relative_mode_set_point_is_as_expected(self):
        expected_channels = {"X": 45, "Y": 65, "Z": 70, "V": 200}

        for channel, rel_set_point in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:RELSMODE:SP".format(channel), rel_set_point)
            self.ca.assert_that_pv_is("LKSH460_01:{0}:RELSMODE".format(channel), rel_set_point)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_relative_mode_set_point_unit_set_WHEN_read_THEN_relative_mode_set_point_unit_is_as_expected(self):
        channels = ["X", "Y", "Z", "V"]
        sample_data = {0: "uG", 1: "mG", 2: "G", 3: "kG"}

        for channel in channels:
            for input, egu in sample_data.iteritems():
                self.ca.set_pv_value("LKSH460_01:{0}:RELS:MULTIPLIER".format(channel), input)
                self.ca.assert_that_pv_is("LKSH460_01:{0}:RELSMODE.EGU".format(channel), egu)

    def test_GIVEN_relative_mode_reading_set_WHEN_read_THEN_relative_mode_reading_is_as_expected(self):
        expected_rel_mode_reading = 500
        self._set_rel_mode_reading(expected_rel_mode_reading)
        channels = ["X", "Y", "Z", "V"]
        for channel in channels:
            self.ca.assert_that_pv_is("LKSH460_01:{0}:RELMODEREADING".format(channel), expected_rel_mode_reading)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_relative_mode_reading_unit_set_WHEN_read_THEN_relative_mode_reading_unit_is_as_expected(self):
        channels = ["X", "Y", "Z", "V"]
        sample_data = {0: "uG", 1: "mG", 2: "G", 3: "kG"}
        for channel in channels:
            for input, egu in sample_data.iteritems():
                self.ca.set_pv_value("LKSH460_01:{0}:RELRM:MULTIPLIER".format(channel), input)
                self.ca.assert_that_pv_is("LKSH460_01:{0}:RELMODEREADING.EGU".format(channel), egu)

    def test_GIVEN_magnetic_field_reading_set_WHEN_read_THEN_magnetic_field_reading_is_as_expected(self):
        expected_field_reading = 400
        self._set_magnetic_field_reading(expected_field_reading)
        self.ca.assert_that_pv_is("LKSH460_01:X:FIELDREADING", expected_field_reading)
        self.ca.assert_that_pv_is("LKSH460_01:Y:FIELDREADING", expected_field_reading)
        self.ca.assert_that_pv_is("LKSH460_01:Z:FIELDREADING", expected_field_reading)
        self.ca.assert_that_pv_is("LKSH460_01:V:FIELDREADING", expected_field_reading)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_magnetic_field_reading_unit_set_WHEN_read_THEN_magnetic_field_reading_unit_is_as_expected(self):
        channels = ["X", "Y", "Z", "V"]
        sample_data = {0: "uG", 1: "mG", 2: "G", 3: "kG"}

        for channel in channels:
            for input, egu in sample_data.iteritems():
                self.ca.set_pv_value("LKSH460_01:{0}:FIELD:MULTIPLIER".format(channel), input)
                self.ca.assert_that_pv_is("LKSH460_01:{0}:FIELDREADING.EGU".format(channel), egu)
