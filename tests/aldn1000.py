import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "ALDN1000_01"
DEVICE_NAME = "aldn1000"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ALDN1000"),
        "macros": {},
        "emulator": DEVICE_NAME,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Aldn1000Tests(unittest.TestCase):
    """
    Tests for the Aldn1000 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device("reset")

    @parameterized.expand([('Value 1', 12.12), ('Value 2', 1.123), ('Value 3', 123.0)])
    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_new_diameter_WHEN_set_diameter_THEN_new_diameter_set(self, _, value):
        expected_diameter = value
        self.ca.set_pv_value("DIAMETER:SP", expected_diameter)

        self.ca.assert_that_pv_is("DIAMETER", expected_diameter, timeout=2)

    @parameterized.expand([('Value 1', 12345), ('Value 2', 1234), ('Value 3', 77424)])
    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_new_invalid_high_diameter_WHEN_set_diameter_THEN_diameter_set_limit_returned(self, _, value):
        invalid_diameter = value
        expected_diameter = 1000.00
        self.ca.set_pv_value("DIAMETER:SP", invalid_diameter)

        self.ca.assert_that_pv_is("DIAMETER", expected_diameter, timeout=2)

    @parameterized.expand([('Value 1', -2345), ('Value 2', -1234), ('Value 3', -676424)])
    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_new_invalid_low_diameter_WHEN_set_diameter_THEN_diameter_set_limit_returned(self, _, value):
        invalid_diameter = value
        expected_diameter = 0.00
        self.ca.set_pv_value("DIAMETER:SP", invalid_diameter)

        self.ca.assert_that_pv_is("DIAMETER", expected_diameter, timeout=2)

    @parameterized.expand([('Value 1', 14.1), ('Value 2', 24.23), ('Value 3', 30)])
    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_new_diameter_above_14mm_WHEN_set_diameter_THEN_volume_units_changed(self, _, value):
        set_diameter = value
        expected_units = 'mL'
        self.ca.set_pv_value("DIAMETER:SP", set_diameter)

        self.ca.assert_that_pv_is("VOLUME:UNITS", expected_units, timeout=2)

    @parameterized.expand([('Value 1', 14.0), ('Value 2', 10.0), ('Value 3', 5.0)])
    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_new_diameter_below_or_eq_14mm_WHEN_set_diameter_THEN_volume_units_changed(self, _, value):
        set_diameter = value
        expected_units = 'uL'
        self.ca.set_pv_value("DIAMETER:SP", set_diameter)

        self.ca.assert_that_pv_is("VOLUME:UNITS", expected_units, timeout=2)

    @parameterized.expand([('Value 1', 0.123), ('Value 2', 1.342), ('Value 3', 12.34)])
    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_new_volume_WHEN_set_volume_THEN_new_volume_set(self, _, value):
        expected_volume = value
        self.ca.set_pv_value("VOLUME:SP", expected_volume)

        self.ca.assert_that_pv_is("VOLUME", expected_volume, timeout=2)

    @parameterized.expand([('Direction 1', 'Withdraw'), ('Direction 2', 'Infuse')])
    def test_GIVEN_new_direction_WHEN_set_direction_THEN_new_direction_set(self, _, direction):
        expected_direction = direction
        self.ca.set_pv_value("DIRECTION:SP", expected_direction)

        self.ca.assert_that_pv_is("DIRECTION", expected_direction)

    @parameterized.expand([('Direction 1', 'Withdraw'), ('Direction 2', 'Infuse')])
    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_direction_WHEN_set_reverse_direction_THEN_direction_reversed(self, _, direction):
        initial_direction = direction
        if initial_direction == 'Infuse':
            expected_direction = 'Withdraw'
        else:
            expected_direction = 'Infuse'
        self.ca.set_pv_value("DIRECTION:SP", direction)
        self.ca.assert_that_pv_is("DIRECTION", direction, timeout=2)
        self.ca.set_pv_value("DIRECTION:SP", 'Reverse')

        self.ca.assert_that_pv_is("DIRECTION", expected_direction, timeout=2)

    @parameterized.expand([('Value 1', 0.123), ('Value 2', 1.342), ('Value 3', 12.34)])
    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_new_rate_WHEN_set_rate_THEN_new_rate_set(self, _, value):
        expected_rate = value
        self.ca.set_pv_value("RATE:SP", expected_rate)

        self.ca.assert_that_pv_is("RATE", expected_rate)

    @parameterized.expand([('Value 1', 2123), ('Value 2', 1411.342), ('Value 3', 1222.34)])
    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_new_invalid_high_rate_WHEN_set_rate_THEN_rate_high_limit_set(self, _, value):
        invalid_rate = value
        expected_rate = 1000.0
        self.ca.set_pv_value("RATE:SP", invalid_rate)

        self.ca.assert_that_pv_is("RATE", expected_rate)

    @parameterized.expand([('Value 1', -9085), ('Value 2', -0.123342), ('Value 3', -5226.31234)])
    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_new_invalid_low_rate_WHEN_set_rate_THEN_rate_high_limit_set(self, _, value):
        invalid_rate = value
        expected_rate = 0.0
        self.ca.set_pv_value("RATE:SP", invalid_rate)

        self.ca.assert_that_pv_is("RATE", expected_rate)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_an_infused_volume_WHEN_get_volume_dispensed_THEN_infused_volume_returned(self):
        expected_infusion_volume = 1.123
        self._lewis.backdoor_set_on_device("volume_infused", expected_infusion_volume)

        self.ca.assert_that_pv_is("VOLUME:INF", expected_infusion_volume, timeout=2)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_infusion_volume_dispensed_WHEN_clear_infused_volume_dispensed_THEN_volume_cleared(self):
        infused_volume_dispensed = 2.342
        expected_volume_dispensed = 0.0
        self._lewis.backdoor_set_on_device("volume_infused", infused_volume_dispensed)
        self.ca.assert_that_pv_is("VOLUME:INF", infused_volume_dispensed, timeout=2)
        self.ca.set_pv_value("VOLUME:INF:CLEAR:SP", "CLEAR")

        self.ca.assert_that_pv_is("VOLUME:INF", expected_volume_dispensed)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_withdrawn_volume_dispensed_WHEN_clear_withdrawn_volume_dispensed_THEN_volume_cleared(self):
        withdrawn_volume_dispensed = 93.12
        expected_volume_dispensed = 0.0
        self._lewis.backdoor_set_on_device("volume_withdrawn", withdrawn_volume_dispensed)
        self.ca.assert_that_pv_is("VOLUME:WDR", withdrawn_volume_dispensed, timeout=2)
        self.ca.set_pv_value("VOLUME:WDR:CLEAR:SP", "CLEAR")

        self.ca.assert_that_pv_is("VOLUME:WDR", expected_volume_dispensed)

    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_pump_off_WHEN_set_pump_on_THEN_pump_turned_on(self):
        status_mode = 'Pumping Program Stopped'
        self.ca.set_pv_value("RUN:SP", "Run")

        self.ca.assert_that_pv_is_not("STATUS", status_mode)

    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_pump_on_WHEN_set_pump_off_THEN_pump_paused(self):
        status_mode = "Infusing"
        expected_status_mode = "Pumping Program Paused"
        self.ca.set_pv_value("VOLUME:SP", 100.00)
        self.ca.set_pv_value("DIRECTION:SP", "Infuse")
        self.ca.set_pv_value("RUN:SP", "Run")
        self.ca.assert_that_pv_is("STATUS", status_mode, timeout=2)

        self.ca.set_pv_value("STOP:SP", "Stop")

        self.ca.assert_that_pv_is("STATUS", expected_status_mode)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_given_program_function_WHEN_program_function_changed_THEN_program_function_updated(self):
        expected_function = 'INCR'
        self._lewis.backdoor_set_on_device('program_function', expected_function)

        self.ca.assert_that_pv_is("PROGRAM:FUNCTION", expected_function, timeout=2)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_an_input_error_WHEN_open_file_THEN_file_error_str_returned(self):
        self._lewis.backdoor_set_on_device("input_correct", False)
        expected_value = "Command N/A currently"
        expected_diameter = 1.123
        self.ca.set_pv_value("DIAMETER:SP", expected_diameter)

        self.ca.assert_that_pv_is("ERROR", expected_value, timeout=2)

    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_device_connected_WHEN_get_status_THEN_device_status_returned(self):
        expected_status = 'Pumping Program Stopped'

        self.ca.assert_that_pv_is("STATUS", expected_status, timeout=2)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_device_not_connected_WHEN_get_error_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.set_pv_value("STATUS.PROC", 1)
        self.ca.assert_that_pv_alarm_is('STATUS', ChannelAccess.Alarms.INVALID, timeout=5)

    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_pump_infusing_WHEN_pump_on_THEN_infused_volume_dispensed_increases(self):
        self.ca.set_pv_value("VOLUME:SP", 10.00)
        self.ca.set_pv_value("RATE:SP", 0.50)
        self.ca.set_pv_value("RATE:UNITS:SP", "uL/min")
        self.ca.set_pv_value("DIRECTION:SP", "Infuse")
        self.ca.set_pv_value("VOLUME:INF:CLEAR:SP", "CLEAR")
        self.ca.set_pv_value("RUN:SP", "Run")

        self.ca.assert_that_pv_is_not("VOLUME:INF", 0.0, timeout=0.0)
        self.ca.set_pv_value("STOP:SP", "Stop")

    @parameterized.expand([("Low limit", 1.0, "uL"), ("High limit", 15.0, "mL")])
    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_diameter_change_WHEN_new_diamater_causes_units_changed_THEN_volume_units_EGU_updated(self, _, value, units):
        expected_units = units
        self.ca.set_pv_value("DIAMETER:SP", value)

        self.ca.assert_that_pv_is("VOLUME.EGU", expected_units)
