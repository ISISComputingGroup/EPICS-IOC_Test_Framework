from __future__ import division
import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc
import itertools

# Device prefix
DEVICE_PREFIX = "KHLY2400_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KHLY2400"),
        "emulator": "keithley_2400",
        "macros": {
    "IEOS": r"\\r\\n",
    "OEOS": r"\\r\\n",
        }
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

TEST_OUTPUTS = [1.23, 456.789, 1e-3, -1.23, -456.789, -1e-3]

RANGE_MAGNITUDES = [10**x for x in range(-6, 1)]


class Keithley2400Tests(unittest.TestCase):
    """
    Tests for the keithley 2400.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2400", DEVICE_PREFIX)

        self._lewis.backdoor_set_on_device("random_output", False)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def calculate_resistance_range(self, value):
        """
        The resistance ranges of the device are 2.1*10^x, where x is between 0 and 8
        """

        for r in [2.1 * 10**i for i in range(1, 8)]:
            if value < r:
                return r / 10

    @skip_if_recsim("Recsim does not work with lewis backdoor tests")
    def test_WHEN_current_value_is_set_THEN_readback_returns_value_just_set(self):
        self.ca.set_pv_value("OUTPUT:MODE:SP", "On")
        for test_val in TEST_OUTPUTS:
            self._lewis.backdoor_set_on_device("current", test_val)
            self.ca.assert_that_pv_is_number("CURR", test_val, tolerance=0.05*abs(test_val))

    @skip_if_recsim("Recsim does not work with lewis backdoor tests")
    def test_WHEN_voltage_value_is_set_THEN_readback_returns_value_just_set(self):
        self.ca.set_pv_value("OUTPUT:MODE:SP", "On")
        for test_val in TEST_OUTPUTS:
            self._lewis.backdoor_set_on_device("voltage", test_val)
            self.ca.assert_that_pv_is_number("VOLT", test_val, tolerance=0.05*abs(test_val))

    @skip_if_recsim("Recsim does not work with lewis backdoor tests")
    def test_WHEN_voltage_and_current_are_set_THEN_readback_returns_valid_resistance(self):
        self.ca.set_pv_value("OUTPUT:MODE:SP", "On")
        for volts, amps in itertools.product([4.5, 6.7], [6.7, 4.5]):
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
        # Write to the RAW pv, test that the CURR pv does not update with the new value when output is off
        self.ca.set_pv_value("CURR:RAW", 1.0)
        self.ca.set_pv_value("OUTPUT:MODE:SP", "Off")

        self._lewis.backdoor_set_on_device("current", 5.0)

        self.ca.assert_that_pv_value_is_unchanged("CURR", 1.0)

    @skip_if_recsim("Recsim does not work with lewis backdoor tests")
    def test_WHEN_output_mode_is_unset_THEN_voltage_readback_does_not_update(self):
        # Write to the RAW value, test that the VOLT pv does not update with the new value when output is off
        self.ca.set_pv_value("VOLT:RAW", 1.0)
        self.ca.set_pv_value("OUTPUT:MODE:SP", "Off")

        self._lewis.backdoor_set_on_device("voltage", 5.0)

        self.ca.assert_that_pv_value_is_unchanged("VOLT", 1.0)

    def test_WHEN_resistance_mode_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for mode in ["Manual", "Auto"]:
            self.ca.assert_setting_setpoint_sets_readback(mode, "RES:MODE")

    def test_WHEN_remote_sensing_mode_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for mode in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(mode, "SENS:MODE")

    def test_WHEN_automatic_range_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for test_val in ["Manual", "Auto"]:
            self.ca.assert_setting_setpoint_sets_readback(test_val, "RES:RANGE:AUTO")

    @skip_if_recsim("Banded record behaviour too complex for recsim")
    def test_WHEN_range_is_set_THEN_readback_updates_with_appropriate_range_for_value_just_set(self):
        for test_val in TEST_OUTPUTS:
            ideal_range = self.calculate_resistance_range(test_val)
            self.ca.set_pv_value("RES:RANGE:SP", test_val)
            self.ca.assert_that_pv_is_number("RES:RANGE", ideal_range, tolerance=0.05 * ideal_range)

    def test_WHEN_source_mode_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for test_val in ["Current", "Voltage"]:
            self.ca.assert_setting_setpoint_sets_readback(test_val, "SOURCE:MODE")

    def test_WHEN_current_compliance_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for test_val in TEST_OUTPUTS:
            self.ca.assert_setting_setpoint_sets_readback(test_val, "CURR:COMPLIANCE")

    def test_WHEN_voltage_compliance_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for test_val in TEST_OUTPUTS:
            self.ca.assert_setting_setpoint_sets_readback(test_val, "VOLT:COMPLIANCE")

    def test_WHEN_source_voltage_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for test_val in TEST_OUTPUTS:
            self.ca.assert_setting_setpoint_sets_readback(test_val, "VOLT:SOURCE")

    def test_WHEN_source_current_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for test_val in TEST_OUTPUTS:
            self.ca.assert_setting_setpoint_sets_readback(test_val, "CURR:SOURCE")

    def test_WHEN_source_current_autoranging_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for test_val in ["Off", "On"]:
            self.ca.assert_setting_setpoint_sets_readback(test_val, "CURR:SOURCE:AUTORANGE")

    def test_WHEN_source_voltage_autoranging_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for test_val in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(test_val, "VOLT:SOURCE:AUTORANGE")

    def test_WHEN_measurement_current_autoranging_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for test_val in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(test_val, "CURR:MEAS:AUTORANGE")

    def test_WHEN_measurement_voltage_autoranging_is_set_THEN_readback_updates_with_the_value_just_set(self):
        for test_val in ["On", "Off"]:
            self.ca.assert_setting_setpoint_sets_readback(test_val, "VOLT:MEAS:AUTORANGE")

    @skip_if_recsim("Banded record behaviour too complex for recsim")
    def test_WHEN_source_current_range_is_set_THEN_readback_updates_with_the_appropriate_range_for_value_just_set(self):
        """
        Current ranges on the KHLY2400 are simply powers of ten, the whole range of which is covered here
        """
        for test_val in RANGE_MAGNITUDES:
            self.ca.set_pv_value("CURR:SOURCE:RANGE:SP", test_val)
            self.ca.assert_that_pv_is_number("CURR:SOURCE:RANGE", test_val, tolerance=0.05 * test_val)

    @skip_if_recsim("Banded record behaviour too complex for recsim")
    def test_WHEN_source_voltage_range_is_set_THEN_readback_updates_with_the_appropriate_range_for_value_just_set(self):
        """
        Voltage ranges on the KHLY2400 are 2*multiples of ten, the whole range is covered here.

        """
        for magnitude in RANGE_MAGNITUDES:
            test_val = 2.*magnitude
            self.ca.set_pv_value("VOLT:SOURCE:RANGE:SP", test_val)
            self.ca.assert_that_pv_is_number("VOLT:SOURCE:RANGE", test_val, tolerance=0.05 * test_val)

    @skip_if_recsim("Banded record behaviour too complex for recsim")
    def test_WHEN_volts_measurement_range_is_set_THEN_readback_updates_with_appropriate_range_for_value_just_set(self):
        """
        Voltage ranges on the KHLY2400 are 2*multiples of ten, the whole range is covered here.

        """
        for magnitude in RANGE_MAGNITUDES:
            test_val = 2.*magnitude
            self.ca.set_pv_value("VOLT:MEAS:RANGE:SP", test_val)
            self.ca.assert_that_pv_is_number("VOLT:MEAS:RANGE", test_val, tolerance=0.05 * test_val)

    @skip_if_recsim("Banded record behaviour too complex for recsim")
    def test_WHEN_current_measurement_range_is_set_THEN_readback_updates_with_appropriate_range_for_value_just_set(self):
        """
        Current ranges on the KHLY2400 are simply powers of ten, the whole range of which is covered here
        """
        for test_val in RANGE_MAGNITUDES:
            self.ca.set_pv_value("CURR:MEAS:RANGE:SP", test_val)
            self.ca.assert_that_pv_is_number("CURR:MEAS:RANGE", test_val, tolerance=0.05 * test_val)
