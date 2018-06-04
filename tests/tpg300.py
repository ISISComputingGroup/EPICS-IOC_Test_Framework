import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim
from enum import Enum
from itertools import product

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


class Units(Enum):
    mbar = 1
    Torr = 2
    Pa = 3


CHANNELS = "A1", "A2", "B1", "B2"
TEST_PRESSURES = 1.23, -10.23, 8, 1e-6, 1e+6


class Tpg300Tests(unittest.TestCase):
    """
    Tests for the TPG300.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tpg300", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._reset_emulators_values()

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
        self._lewis.backdoor_set_on_device("units", unit.value)
        self._ioc.set_simulated_value("SIM:UNITS", unit.name)

    def _set_connected(self, connected):
        self._lewis.backdoor_set_on_device("connected", connected)

    def test_WHEN_ioc_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_units_are_set_THEN_unit_is_the_same_as_backdoor(self):
        for unit in Units:
            expected_unit = unit.name
            self._set_units(unit)
            self.ca.assert_that_pv_is("UNITS", expected_unit)

    def test_that_GIVEN_pressure_value_WHEN_set_via_backdoor_THEN_updates_in_ioc(self):
        for expected_pressure, channel in product(TEST_PRESSURES, CHANNELS):
            pv = "PRESSURE_{}".format(channel)
            self._set_pressure(expected_pressure, channel)
            self.ca.assert_that_pv_is(pv, expected_pressure)

    @skip_if_recsim("Recsim is unable to simulate a disconnected device")
    def test_GIVEN_asked_for_units_WHEN_emulator_is_disconnected_THEN_ca_alarm_shows_disconnected(self):
        self._set_connected(False)

        for channel in CHANNELS:
            pv = "PRESSURE_{}".format(channel.upper())
            self.ca.assert_pv_alarm_is(pv, ChannelAccess.ALARM_INVALID)

