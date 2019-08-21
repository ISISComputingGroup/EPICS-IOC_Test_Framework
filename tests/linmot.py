import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "LINMOT_01"
DEVICE_NAME = "linmot"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LINMOT"),
        "macros": {
            "MTRCTRL": "1",
            "AXIS1": "yes",
        },
        "emulator": DEVICE_NAME,
    },
]


TEST_MODES = [TestModes.DEVSIM]


class LinmotTests(unittest.TestCase):
    """
    Tests for the _Device_ IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self.ca_linmot = ChannelAccess(default_timeout=30, device_prefix="MOT")

    @skip_if_recsim("Lewis backdoor not available in RECSIM mode")
    def test_GIVEN_motor_destination_WHEN_motor_given_destination_THEN_move_to_correct_place(self):
        expected_value = 5
        # this gives the computer the set point
        self.ca_linmot.set_pv_value("MTR0101:SP", expected_value)
        # this shows what the readback value was (it should be the same as the setpoint
        self.ca_linmot.assert_that_pv_is("MTR0101", expected_value, timeout=2)

    def test_GIVEN_velocity_WHEN_started_up_THEN_velocity_is_correct(self):
        expected_value = 0.1
        self.ca_linmot.assert_that_pv_is("MTR0101.VELO", expected_value, timeout=2)
