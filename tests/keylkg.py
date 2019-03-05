import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "KEYLKG_01"
EMULATOR_NAME = "keylkg"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KEYLKG"),
        "macros": {},
        "emulator": EMULATOR_NAME,
    },
]


TEST_MODES = [TestModes.DEVSIM]


class KeylkgTests(unittest.TestCase):
    """
    Tests for the Keylkg IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device("reset")

    def test_GIVEN_running_ioc_WHEN_change_to_communication_mode_THEN_mode_changed(self):
        expected_value = "COMMUNICATION"
        self.ca.set_pv_value("MODE:SP", expected_value)

        self.ca.assert_that_pv_is("MODE", expected_value, timeout=2)

    def test_GIVEN_running_ioc_WHEN_change_to_normal_mode_THEN_mode_changed(self):
        expected_value = "NORMAL"
        self.ca.set_pv_value("MODE:SP", expected_value)

        self.ca.assert_that_pv_is("MODE", expected_value, timeout=2)

    def test_GIVE_running_ioc_WHEN_set_output1_offset_THEN_output1_offset_updated(self):
        expected_value = 1.123
        self.ca.set_pv_value("OFFSET:OUTPUT:1:SP", expected_value)

        self.ca.assert_that_pv_is("OFFSET:OUTPUT:1", expected_value, timeout=2)

    def test_GIVE_running_ioc_WHEN_set_output2_offset_THEN_output1_offset_updated(self):
        expected_value = 4.2323
        self.ca.set_pv_value("OFFSET:OUTPUT:2:SP", expected_value)

        self.ca.assert_that_pv_is("OFFSET:OUTPUT:2", expected_value, timeout=2)

    def test_GIVEN_running_ioc_WHEN_change_to_head1_measurement_mode_THEN_mode_changed(self):
        expected_value = "MULTI-REFLECTIVE"
        self.ca.set_pv_value("MEASUREMODE:HEAD:A:SP", expected_value)

        self.ca.assert_that_pv_is("MEASUREMODE:HEAD:A", expected_value, timeout=2)

    def test_GIVEN_running_ioc_WHEN_change_to_head2_measurement_mode_THEN_mode_changed(self):
        expected_value = "TRANSPARENT OBJ 1"
        self.ca.set_pv_value("MEASUREMODE:HEAD:B:SP", expected_value)

        self.ca.assert_that_pv_is("MEASUREMODE:HEAD:B", expected_value, timeout=2)
