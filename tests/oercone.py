import unittest
from time import sleep

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list
from enum import Enum


DEVICE_PREFIX = "OERCONE_01"

TEST_PRESSURE_VALUES = [1.0, 17.0, 100.0, 300.0]

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("OERCONE"),
        "macros": {},
        "emulator": "oercone",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Units(Enum):
    mbar = 0
    Torr = 1
    Pascal = 2
    Micron = 3


class OerconeTests(unittest.TestCase):
    """
    Tests for the Oercone IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(IOCS[0]["emulator"], DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_device_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(TEST_PRESSURE_VALUES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_pressure_is_set_via_backdoor_THEN_readback_updates(self, _, pressure):
        self._lewis.backdoor_set_on_device("pressure", pressure)
        self.ca.assert_that_pv_is_number("PRESSURE", pressure)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_measurement_units_is_set_via_backdoor_THEN_readback_updates(self):
        for units in Units:
            self._lewis.backdoor_run_function_on_device("backdoor_set_units", [units.value])
            expected_units = units.name
            self.ca.assert_that_pv_is("PRESSURE.EGU", expected_units)

    @parameterized.expand(parameterized_list(Units))
    def test_WHEN_units_setpoint_set_THEN_read_back_is_correct(self, _, units):
        self.ca.assert_setting_setpoint_sets_readback(units.name, "UNITS")



