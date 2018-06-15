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

        self._lewis.backdoor_set_on_device("random_output", False)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        self.log.info("Message")

    def calculate_resistance_range(self, value):
        for r in [2.1 * pow(10, i) for i in range(1, 8)]:
            if value < r:
                return r / 10

    @skip_if_recsim("Recsim does not work with lewis backdoor tests")
    def test_WHEN_current_value_is_set_THEN_readback_returns_value_just_set(self):
        self.ca.set_pv_value("OUTPUT:MODE:SP", "On")
        for val in [1.23, 456.789, 1e-3]:
            self._lewis.backdoor_set_on_device("current", val)
            self.ca.assert_that_pv_is_number("CURR:RAW", val, tolerance=0.05*val)

    @skip_if_recsim("Recsim does not work with lewis backdoor tests")
    def test_WHEN_voltage_value_is_set_THEN_readback_returns_value_just_set(self):
        self.ca.set_pv_value("OUTPUT:MODE:SP", "On")
        for val in [1.23, 456.789, 1e-3]:
            self._lewis.backdoor_set_on_device("voltage", val)
            self.ca.assert_that_pv_is_number("VOLT:RAW", val, tolerance=0.05*val)

    @skip_if_recsim("Recsim does not work with lewis backdoor tests")
    def test_WHEN_voltage_and_current_are_set_THEN_readback_returns_valid_resistance(self):
        self.ca.set_pv_value("OUTPUT:MODE:SP", "On")
        for volts in [4.5, 6.7]:
            for amps in [6.7, 4.5]:
                self._lewis.backdoor_set_on_device("current", amps)
                self._lewis.backdoor_set_on_device("voltage", volts)

                resistance = volts/amps

                self.ca.assert_that_pv_is_number("RES", resistance, tolerance=0.05*resistance)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_output_mode_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for mode in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(mode, "OUTPUT:MODE")

    @skip_if_recsim("Recsim does not work with lewis backdoor tests")
    def test_WHEN_output_mode_is_unset_THEN_current_readback_does_not_update(self):
        self.ca.set_pv_value("CURR:RAW", 1.0)
        self.ca.set_pv_value("OUTPUT:MODE:SP", "Off")

        self._lewis.backdoor_set_on_device("current", 5.0)

        self.ca.assert_that_pv_is_number("CURR:RAW", 1.0)

    @skip_if_recsim("Recsim does not work with lewis backdoor tests")
    def test_WHEN_output_mode_is_unset_THEN_voltage_readback_does_not_update(self):
        self.ca.set_pv_value("VOLT:RAW", 1.0)
        self.ca.set_pv_value("OUTPUT:MODE:SP", "Off")

        self._lewis.backdoor_set_on_device("voltage", 5.0)

        self.ca.assert_that_pv_is_number("VOLT:RAW", 1.0)

    def test_WHEN_resistance_mode_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for mode in ["Manual", "Auto"]:
            self.ca.assert_setting_setpoint_sets_readback(mode, "RES:MODE")

    def test_WHEN_remote_sensing_mode_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for mode in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(mode, "SENS:MODE")

    def test_WHEN_automatic_range_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in ["Manual", "Auto"]:
            self.ca.assert_setting_setpoint_sets_readback(val, "RES:RANGE:AUTO")

    @skip_if_recsim("Banded record behaviour too complex for recsim")
    def test_WHEN_range_is_set_THEN_readback_updates_with_appropriate_range_for_value_just_set(self):
        for val in [1.23, 456.789, 1e-3]:
            ideal_range = self.calculate_resistance_range(val)
            self.ca.set_pv_value("RES:RANGE:SP", val)
            self.ca.assert_that_pv_is_number("RES:RANGE:SP:RBV", ideal_range, tolerance=0.05 * ideal_range)

    def test_WHEN_source_mode_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in ["Current", "Voltage"]:
            self.log.info("SOURCE:MODE")
            self.ca.assert_setting_setpoint_sets_readback(val, "SOURCE:MODE")

    def test_WHEN_current_compliance_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in [1.23, 456.789, 1e-6, -1e-6]:
            self.ca.assert_setting_setpoint_sets_readback(val, "CURR:COMPLIANCE")

    def test_WHEN_voltage_compliance_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in [1.23, 456.789, 1e-5, -1e-5]:
            self.ca.assert_setting_setpoint_sets_readback(val, "VOLT:COMPLIANCE")

    def test_WHEN_source_voltage_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in [1.23, 456.789, 1e-5, -1e-5]:
            self.ca.assert_setting_setpoint_sets_readback(val, "VOLT:SOURCE")

    def test_WHEN_source_current_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in [0.1, -0.1, 1e-6, -1e-6]:
            self.ca.assert_setting_setpoint_sets_readback(val, "CURR:SOURCE")

    def test_WHEN_source_current_autoranging_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for val in ["Off", "On"]:
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

    @skip_if_recsim("Banded record behaviour too complex for recsim")
    def test_WHEN_source_current_range_is_set_THEN_readback_updates_with_the_appropriate_range_for_value_just_set(self):
        for val in [1.0*pow(10, i) for i in range(-6, 1)]:
            self.ca.set_pv_value("CURR:SOURCE:RANGE:SP", val)
            self.ca.assert_that_pv_is_number("CURR:SOURCE:RANGE:SP:RBV", val, tolerance=0.05 * val)

    @skip_if_recsim("Banded record behaviour too complex for recsim")
    def test_WHEN_source_voltage_range_is_set_THEN_readback_updates_with_the_appropriate_range_for_value_just_set(self):
        for val in [2.0*pow(10, i) for i in range(-6, 1)]:
            self.ca.set_pv_value("VOLT:SOURCE:RANGE:SP", val)
            self.ca.assert_that_pv_is_number("VOLT:SOURCE:RANGE:SP:RBV", val, tolerance=0.05 * val)

    @skip_if_recsim("Banded record behaviour too complex for recsim")
    def test_WHEN_volts_measurement_range_is_set_THEN_readback_updates_with_appropriate_range_for_value_just_set(self):
        for val in [2.0 * pow(10, i) for i in range(-6, 1)]:
            self.ca.set_pv_value("VOLT:MEAS:RANGE:SP", val)
            self.ca.assert_that_pv_is_number("VOLT:MEAS:RANGE:SP:RBV", val, tolerance=0.05 * val)

    @skip_if_recsim("Banded record behaviour too complex for recsim")
    def test_WHEN_current_measurement_range_is_set_THEN_readback_updates_with_appropriate_range_for_value_just_set(self):
        for val in [1.0 * pow(10, i) for i in range(-6, 1)]:
            self.ca.set_pv_value("CURR:MEAS:RANGE:SP", val)
            self.ca.assert_that_pv_is_number("CURR:MEAS:RANGE:SP:RBV", val, tolerance=0.05 * val)
