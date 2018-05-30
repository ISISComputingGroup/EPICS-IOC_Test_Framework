import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "TPG300_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TPG300"),
        "macros": {},
        "emulator": "tpg300",
        "emulator_protocol": "stream",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

UNITS = {
    1: "mbar",
    2: "Torr",
    3: "Pa"
}

CHANNELS = ("A1", "A2", "B1", "B2")


class Tpg300Tests(unittest.TestCase):
    """
    Tests for the TPG300.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tpg300", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._reset_values()

    def _reset_emulators_values(self):
        self._lewis.backdoor_set_on_device("pressure_a1", 1.0)
        self._lewis.backdoor_set_on_device("pressure_a2", 2.0)
        self._lewis.backdoor_set_on_device("pressure_b1", 3.0)
        self._lewis.backdoor_set_on_device("pressure_b2", 4.0)
        self._set_connected(True)

    def _set_pressure(self, expected_pressure, channel):
        prop = "pressure_{}".format(channel.lower())
        pv = "SIM:PRESSURE"
        self._lewis.backdoor_set_on_device(prop, expected_pressure)
        self._ioc.set_simulated_value(pv, expected_pressure)

    def _set_units(self, unit):
        self._lewis.backdoor_set_on_device("units", unit)
        self._ioc.set_simulated_value("SIM:UNITS", UNITS[unit])

    def _set_connected(self, connected):
        self._lewis.backdoor_set_on_device("connected", connected)

    def test_WHEN_ioc_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_units_are_set_THEN_unit_is_the_same_as_backdoor(self):
        for unit_flag, unit_string in UNITS.items():
            expected_unit = unit_string
            self._set_units(unit_flag)
            self.ca.assert_that_pv_is("UNITS", expected_unit)

    def test_GIVEN_floating_point_pressure_value_WHEN_pressure_is_read_THEN_pressure_value_is_same_as_backdoor(self):
        expected_pressure = 1.23

        for channel in CHANNELS:
            pv = "PRESSURE_{}".format(channel.upper())

            self._set_pressure(expected_pressure, channel)

            self.ca.assert_that_pv_is(pv, expected_pressure)

    def test_GIVEN_negative_floating_point_pressure_value_WHEN_pressure_is_read_THEN_pressure_value_is_same_as_backdoor(self):
        expected_pressure = -10.23

        for channel in CHANNELS:
            pv = "PRESSURE_{}".format(channel.upper())

            self._set_pressure(expected_pressure, channel)

            self.ca.assert_that_pv_is(pv, expected_pressure)

    def test_GIVEN_integer_pressure_value_WHEN_pressure_is_read_THEN_pressure_value_is_same_as_backdoor(self):
        expected_pressure = 8

        for channel in CHANNELS:
            pv = "PRESSURE_{}".format(channel.upper())

            self._set_pressure(expected_pressure, channel)

            self.ca.assert_that_pv_is(pv, expected_pressure)

    def test_GIVEN_pressure_in_negative_exponential_form_WHEN_pressure_is_read_THEN_pressure_value_is_same_as_backdoor(self):
        expected_pressure = 1e-6

        for channel in CHANNELS:
            pv = "PRESSURE_{}".format(channel.upper())

            self._set_pressure(expected_pressure, channel)

            self.ca.assert_that_pv_is(pv, expected_pressure)

    def test_GIVEN_pressure_in_positive_exponential_form_WHEN_pressure_is_read_THEN_pressure_value_is_same_as_backdoor(self):
        expected_pressure = 1e+6

        for channel in CHANNELS:
            pv = "PRESSURE_{}".format(channel.upper())

            self._set_pressure(expected_pressure, channel)

            self.ca.assert_that_pv_is(pv, expected_pressure)

    @skip_if_recsim("This test fails in recsim")
    def test_GIVEN_asked_for_units_WHEN_emulator_is_disconnected_THEN_ca_alarm_shows_disconnected(self):
        self._set_connected(False)
        self.ca.assert_pv_alarm_is('PRESSURE_A1', ChannelAccess.ALARM_INVALID)

