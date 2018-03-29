import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "PDR2000_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("PDR2000"),
        "macros": {},
        "emulator": "Pdr2000",
    },
]


TEST_MODES = [TestModes.RECSIM]


class Pdr2000Tests(unittest.TestCase):
    """
    Tests for the Pdr2000 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Pdr2000", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_GIVEN_version_set_WHEN_read_THEN_version_is_as_set(self):
        set_version = "test_version"
        self.ca.set_pv_value("SIM:VERSION", set_version)
        self.ca.assert_that_pv_is("VERSION", set_version)

    def test_GIVEN_units_set_WHEN_read_THEN_units_is_as_set(self):
        set_units = "test_units"
        self.ca.set_pv_value("SIM:UNITS", set_units)
        self.ca.assert_that_pv_is("UNITS", set_units)

    def test_GIVEN_pres_set_WHEN_read_THEN_pres_is_as_set(self):
        set_pres = 123.45
        self.ca.set_pv_value("SIM:PRES:1", set_pres)
        self.ca.assert_that_pv_is("PRES:1", set_pres)

    def test_GIVEN_pres_set_WHEN_read_THEN_pres_is_as_set(self):
        set_pres = 123.45
        self.ca.set_pv_value("SIM:PRES:2", set_pres)
        self.ca.assert_that_pv_is("PRES:2", set_pres)

    def test_GIVEN_scale_set_WHEN_read_THEN_scale_is_as_set(self):
        set_scale = 123.45
        self.ca.set_pv_value("SIM:SCALE:1", set_scale)
        self.ca.assert_that_pv_is("SCALE:1", set_scale)

    def test_GIVEN_scale_set_WHEN_read_THEN_scale_is_as_set(self):
        set_scale = 123.45
        self.ca.set_pv_value("SIM:SCALE:2", set_scale)
        self.ca.assert_that_pv_is("SCALE:2", set_scale)