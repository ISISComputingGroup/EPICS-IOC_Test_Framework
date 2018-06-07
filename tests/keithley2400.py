import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc
from lewis.core.logging import has_log
from math import pow

# Device prefix
DEVICE_PREFIX = "KHLY2400_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KHLY2400"),
        "emulator": "keithley_2400"
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

@has_log
class Keithley2400Tests(unittest.TestCase):
    """
    Tests for the keithley 2400.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2400", DEVICE_PREFIX)
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        self.log.info("Message")

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
            self.log.info("SOURCE:MODE")
            self.ca.assert_setting_setpoint_sets_readback(val, "SOURCE:MODE")

    def test_WHEN_current_compliance_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in [1.23, 456.789]:
            self.ca.assert_setting_setpoint_sets_readback(val, "I:COMPLIANCE")

    def test_WHEN_voltage_compliance_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in [1.23, 456.789]:
            self.ca.assert_setting_setpoint_sets_readback(val, "V:COMPLIANCE")

    def test_WHEN_source_voltage_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in [1.23, 456.789]:
            self.log.info('Setpoint value: {}'.format(val))
            self.ca.assert_setting_setpoint_sets_readback(val, "VOLT:SOURCE")

    def test_WHEN_source_current_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in [0.1, -0.1]:
            self.ca.assert_setting_setpoint_sets_readback(val, "CURR:SOURCE")

    def test_WHEN_source_current_autoranging_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(val, "CURR:SOURCE:AUTORANGE")

    def test_WHEN_source_voltage_autoranging_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(val, "VOLT:SOURCE:AUTORANGE")

    def test_WHEN_measurement_current_autoranging_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(val, "CURR:MEAS:AUTORANGE")

    def test_WHEN_measurement_voltage_autoranging_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(val, "VOLT:MEAS:AUTORANGE")

    def test_WHEN_source_current_range_is_set_THEN_readback_updates_with_the_appropriate_range_for_value_just_set(self):
        for val in [1.05*pow(10, i) for i in range(-6, 1)]:
            self.ca.assert_setting_setpoint_sets_readback(val, "CURR:SOURCE:RANGE")

    def test_WHEN_source_voltage_range_is_set_THEN_readback_updates_with_the_appropriate_range_for_value_just_set(self):
        for val in [2.1*pow(10, i) for i in range(-6, 1)]:
            self.ca.assert_setting_setpoint_sets_readback(val, "VOLT:SOURCE:RANGE")

    def test_WHEN_volts_measurement_range_is_set_THEN_readback_updates_with_appropriate_range_for_value_just_set(self):
        for val in [2.1 * pow(10, i) for i in range(-6, 1)]:
            self.ca.assert_setting_setpoint_sets_readback(val, "VOLT:MEAS:RANGE")

    def test_WHEN_current_measurement_range_is_set_THEN_readback_updates_with_appropriate_range_for_value_just_set(self):
        for val in [1.05 * pow(10, i) for i in range(-6, 1)]:
            self.ca.assert_setting_setpoint_sets_readback(val, "CURR:MEAS:RANGE")
