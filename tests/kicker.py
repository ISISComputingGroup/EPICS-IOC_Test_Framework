from parameterized import parameterized
import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list

DEVICE_PREFIX = "KICKER_01"

# VOLTAGE CALIBRATION CONTSTANTS FOR TESTS
DAQ_MAX_VOLTAGE = 10.0
PSU_MAX_VOLTAGE = 45.0  # This is set as a macro in IOC st.cmd
VOLTAGE_CALIBRATION_RATIO = PSU_MAX_VOLTAGE / DAQ_MAX_VOLTAGE


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KICKER"),
        "macros": {},
    },
]


TEST_MODES = [TestModes.RECSIM]


class KickerVoltageTests(unittest.TestCase):
    """
    Tests for the Kicker IOC.
    """
    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

    def _set_voltage(self, value):
        self.ca.set_pv_value("DAQ:R00:DATA:SIM", value)
        self.ca.assert_that_pv_is("DAQ:R00:DATA:_RAW", value)

    @parameterized.expand(
        parameterized_list([
            (4.68, 4.68 * VOLTAGE_CALIBRATION_RATIO),
            (10, 10 * VOLTAGE_CALIBRATION_RATIO),
            (0, 0 * VOLTAGE_CALIBRATION_RATIO),
            (4e-5, 4e-5 * VOLTAGE_CALIBRATION_RATIO)
        ])
    )
    def test_that_GIVEN_a_voltage_THEN_the_calibrated_voltage_is_read(self, _, voltage_to_set, expected_voltage):
        # Given:
        self._set_voltage(voltage_to_set)

        # Then:
        self.ca.assert_that_pv_is("VOLT", expected_voltage)

    def test_that_GIVEN_a_voltage_out_of_range_THEN_voltage_is_in_alarm(self, voltage_to_set=15):
        # Given:
        self._set_voltage(voltage_to_set)

        # Then:
        self.ca.assert_that_pv_alarm_is("VOLT", self.ca.Alarms.MAJOR)



