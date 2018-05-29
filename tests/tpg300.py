import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
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


TEST_MODES = [TestModes.RECSIM]


UNITS = ["mbar", "Torr"]


class Tpg300Tests(unittest.TestCase):
    """
    Tests for the TPG300.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)

        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

    def test_WHEN_ioc_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_units_are_set_THEN_unit_readback_is_the_value_that_was_just_set(self):
        for unit in UNITS:
            self.ca.set_pv_value("UNITS:SP", unit)
            self.ca.assert_that_pv_is("UNITS", unit)

    def test_WHEN_read_pressure_A1_THEN_pressure_A1_value_is_same_as_backdoor(self):
        expected_pressure = 10.0
        self.ca.assert_that_pv_is(PA1_PV, expected_pressure)
