import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import skip_if_recsim, skip_if_devsim

# Device prefix
DEVICE_PREFIX = "ASTRIUM_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ASTRIUM")
    },
]


TEST_MODES = [TestModes.RECSIM]


class AstriumTests(unittest.TestCase):
    """
    Tests for the Astrium Chopper.
    """

    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_phase_set_to_10_p_5_THEN_phase_readback_is_10_p_5(self):
        expected_phase = 10.5
        self.ca.set_pv_value("CH1:PHAS:SP", expected_phase)
        self.ca.assert_that_pv_is("CH1:PHAS", expected_phase)

    def test_WHEN_frequency_set_to_100_THEN_freq_readback_is_100(self):
        expected_freq = 100
        self.ca.set_pv_value("CH1:FREQ:SP", expected_freq)
        self.ca.assert_that_pv_is("CH1:FREQ", expected_freq)

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
        self.ca.set_pv_value("CH1:STATE", "NOT_ESTOP")
        self.ca.assert_that_pv_is("CALIB.STAT", self.ca.Alarms.DISABLE)

    @skip_if_devsim("No backdoor to state in devsim")
    def test_WHEN_both_channels_state_ESTOP_THEN_calibration_enabled(self):
        self.ca.set_pv_value("CH1:STATE", "ESTOP")
        self.ca.set_pv_value("CH2:STATE", "ESTOP")
        self.ca.assert_that_pv_is("CALIB.STAT", self.ca.Alarms.NONE)
