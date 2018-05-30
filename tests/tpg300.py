import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc


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


UNITS = ["mbar", "Torr", "Pa"]


class Tpg300Tests(unittest.TestCase):
    """
    Tests for the TPG300.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tpg300", DEVICE_PREFIX)

        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

    def _set_pressure(self, expected_pressure, letter, channel):
        pv = "SIM:PRESSURE"
        prop = "pressure_{}{}".format(letter, channel)
        self._lewis.backdoor_set_on_device(prop, expected_pressure)
        self._ioc.set_simulated_value(pv, expected_pressure)

    def test_WHEN_ioc_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_units_are_set_THEN_unit_readback_is_the_value_that_was_just_set(self):
        for unit in UNITS:
            self._set_units(unit)
            self.ca.assert_that_pv_is("UNITS", unit)

    def test_GIVEN_floating_point_pressure_value_WHEN_pressure_a1_is_read_THEN_pressure_a1_value_is_same_as_backdoor(self):
        expected_pressure = 1.23
        self._set_pressure(expected_pressure, "a", 1)

        self.ca.assert_that_pv_is("PRESSURE_A1", expected_pressure)

    def test_GIVEN_negative_floating_point_pressure_value_WHEN_pressure_a1_is_read_THEN_pressure_a1_value_is_same_as_backdoor(self):
        expected_pressure = -10.23
        self._set_pressure(expected_pressure, "a", 1)

        self.ca.assert_that_pv_is("PRESSURE_A1", expected_pressure)

    def test_GIVEN_integer_pressure_WHEN_pressure_a1_is_read_THEN_pressure_A1_value_is_same_as_backdoor(self):
        expected_pressure = 8
        self._set_pressure(expected_pressure, "a", 1)

        self.ca.assert_that_pv_is("PRESSURE_A1", expected_pressure)

    def test_GIVEN_pressure_in_negative_exponential_form_WHEN_pressure_a1_is_read_THEN_pressure_A1_value_is_same_as_backdoor(self):
        expected_pressure = 1e-6
        self._set_pressure(expected_pressure, "a", 1)

        self.ca.assert_that_pv_is("PRESSURE_A1", expected_pressure)

    def test_GIVEN_pressure_in_positive_exponential_form_WHEN_pressure_a1_is_read_THEN_pressure_A1_value_is_same_as_backdoor(self):
        expected_pressure = 1e+6
        self._set_pressure(expected_pressure, "a", 1)

        self.ca.assert_that_pv_is("PRESSURE_A1", expected_pressure)

