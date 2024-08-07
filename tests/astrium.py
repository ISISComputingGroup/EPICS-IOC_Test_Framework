import unittest

from parameterized import parameterized

from utils.build_architectures import BuildArchitectures
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list, skip_if_devsim, skip_if_recsim

# Device prefix
DEVICE_PREFIX = "ASTRIUM_01"

IOCS = [
    {"name": DEVICE_PREFIX, "directory": get_default_ioc_dir("ASTRIUM")},
]


# Can only be set in multiples of 10
VALID_FREQUENCIES = [20, 140, 280, 0]

VALID_PHASE_DELAYS = [0.0, 0.01, 123.45, 999.99]


# Devsim for this device is not a usual lewis emulator but puts the actual IOC into a sort of simulation mode.
TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]
BUILD_ARCHITECTURES = [BuildArchitectures._64BIT]


class AstriumTests(unittest.TestCase):
    """
    Tests for the Astrium Chopper.
    """

    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)

    @parameterized.expand(parameterized_list(VALID_FREQUENCIES))
    def test_that_WHEN_setting_the_frequency_setpoint_THEN_it_is_set(self, _, value):
        self.ca.set_pv_value("CH1:FREQ:SP", value)
        self.ca.assert_that_pv_is("CH1:FREQ", value)

    @parameterized.expand(parameterized_list(VALID_PHASE_DELAYS))
    def test_that_WHEN_setting_the_phase_setpoint_THEN_it_is_set(self, _, value):
        self.ca.set_pv_value("CH1:PHASE:SP", value)
        self.ca.assert_that_pv_is("CH1:PHASE", value)

    @parameterized.expand(parameterized_list(VALID_PHASE_DELAYS))
    @skip_if_recsim("Behaviour of phase readback not implemented in recsim")
    def test_that_WHEN_setting_the_phase_setpoint_and_then_speed_THEN_phases_to_the_correct_place(
        self, _, value
    ):
        """
        This test simulates the bug in https://github.com/ISISComputingGroup/IBEX/issues/4123
        """

        # Arrange - set initial speed and phase
        old_speed = 10
        self.ca.set_pv_value("CH1:FREQ:SP", old_speed)
        self.ca.assert_that_pv_is_number("CH1:FREQ", old_speed)  # Wait for it to get there
        self.ca.set_pv_value("CH1:PHASE:SP", value)
        self.ca.assert_that_pv_is_number("CH1:PHASE", value)
        self.ca.assert_that_pv_is_number("CH1:PHASE:SP:RBV", value)

        # Act - set frequency
        new_speed = 20
        self.ca.set_pv_value("CH1:FREQ:SP", new_speed)
        self.ca.assert_that_pv_is_number("CH1:FREQ", new_speed)  # Wait for it to get there

        # Assert - both the actual phase and the setpoint readback should be correct after setting speed.
        self.ca.assert_that_pv_is_number("CH1:PHASE", value)
        self.ca.assert_that_pv_value_is_unchanged("CH1:PHASE", wait=10)
        self.ca.assert_that_pv_is_number("CH1:PHASE:SP:RBV", value)
        self.ca.assert_that_pv_value_is_unchanged("CH1:PHASE:SP:RBV", wait=10)

    def test_WHEN_frequency_set_to_180_THEN_actual_setpoint_not_updated(self):
        sent_frequency = 180
        self.ca.set_pv_value("CH1:FREQ:SP", sent_frequency)
        self.ca.assert_that_pv_is_not("CH1:FREQ:SP_ACTUAL", sent_frequency)
        self.ca.assert_that_pv_is_not("CH1:FREQ", sent_frequency)

    @skip_if_recsim("No state changes in recsim")
    def test_WHEN_brake_called_THEN_state_is_BRAKE(self):
        self.ca.set_pv_value("CH1:BRAKE", 1)
        self.ca.assert_that_pv_is("CH1:STATE", "BRAKE")

    @skip_if_recsim("No state changes in recsim")
    def test_WHEN_speed_set_THEN_state_is_POSITION(self):
        self.ca.set_pv_value("CH1:FREQ:SP", 10)
        self.ca.assert_that_pv_is("CH1:STATE", "POSITION")

    @skip_if_devsim("No backdoor to state in devsim")
    def test_WHEN_one_channel_state_not_ESTOP_THEN_calibration_disabled(self):
        self.ca.set_pv_value("CH1:SIM:STATE", "NOT_ESTOP")
        self.ca.set_pv_value("CH2:SIM:STATE", "E_STOP")
        # Need to process to update disabled status.
        # We don't want the db to process when disabled changes as this will write to the device.
        self.ca.process_pv("CALIB")
        self.ca.assert_that_pv_is("CALIB.STAT", self.ca.Alarms.DISABLE, timeout=1)

    @skip_if_devsim("No backdoor to state in devsim")
    def test_WHEN_both_channels_state_ESTOP_THEN_calibration_enabled(self):
        self.ca.set_pv_value("CH1:SIM:STATE", "E_STOP")
        self.ca.set_pv_value("CH2:SIM:STATE", "E_STOP")
        # Need to process to update disabled status.
        # We don't want the db to process when disabled changes as this will write to the device.
        self.ca.process_pv("CALIB")
        self.ca.assert_that_pv_is_not("CALIB.STAT", self.ca.Alarms.DISABLE, timeout=1)
