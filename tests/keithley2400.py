import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "KHLY2400_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KHLY2400"),
    },
]


TEST_MODES = [TestModes.RECSIM]


class Keithley2400Tests(unittest.TestCase):
    """
    Tests for the keithley 2400.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_output_mode_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for mode in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(mode, "OUTPUT:MODE")

    def test_WHEN_resistance_mode_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for mode in ["Manual", "Auto"]:
            self.ca.assert_setting_setpoint_sets_readback(mode, "RES:MODE")

    def test_WHEN_remote_sensing_mode_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for mode in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(mode, "SENS:MODE")

    def test_WHEN_automatic_range_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in ["Manual", "Auto"]:
            self.ca.assert_setting_setpoint_sets_readback(val, "RES:RANGE:AUTO")

    def test_WHEN_range_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in [1.23, 456.789]:
            self.ca.assert_setting_setpoint_sets_readback(val, "RES:RANGE")

    def test_WHEN_source_mode_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in ["Current", "Voltage"]:
            self.ca.assert_setting_setpoint_sets_readback(val, "SOURCE:MODE")

    def test_WHEN_current_compliance_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in [1.23, 456.789]:
            self.ca.assert_setting_setpoint_sets_readback(val, "I:COMPLIANCE")

    def test_WHEN_voltage_compliance_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in [1.23, 456.789]:
            self.ca.assert_setting_setpoint_sets_readback(val, "V:COMPLIANCE")
