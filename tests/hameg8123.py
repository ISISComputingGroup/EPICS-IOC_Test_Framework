import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "HAMEG8123_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HAMEG8123"),
        "macros": {},
        "emulator": "Hameg8123",
    },
]


TEST_MODES = [TestModes.RECSIM]


class Hameg8123Tests(unittest.TestCase):
    """
    Tests for the Hameg8123 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(None, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_desired_impedence_WHEN_set_impedence_THEN_readback_and_measured_impedence_are_set_to_desired_impedence(
        self,
    ):
        expected_impedance = "50"

        self.ca.assert_setting_setpoint_sets_readback(
            expected_impedance, "CHAN_A:IMPEDANCE:SP:RBV", "CHAN_A:IMPEDANCE:SP"
        )
        self.ca.assert_that_pv_is("CHAN_A:IMPEDANCE", expected_impedance)
