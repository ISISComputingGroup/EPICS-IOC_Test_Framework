import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "SKFMB350_01"

TEST_FREQUENCIES = [0, 17, 258, 10000]
TEST_PHASES = [0, 17, 258, 10000]


class Skf_mb350_chopperTests(unittest.TestCase):
    """
    Tests for the SKF MB350 Chopper IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("skf_mb350_chopper")
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

        self.ca.wait_for("1:FREQ", timeout=30)

    def test_WHEN_frequency_is_set_THEN_actual_frequency_gets_to_the_frequency_just_set(self):
        for frequency in TEST_FREQUENCIES:
            self.ca.set_pv_value("1:FREQ:SP", frequency)
            self.ca.assert_that_pv_is_number("1:FREQ:SP", frequency, 0.01)
            self.ca.assert_that_pv_is_number("1:FREQ", frequency, 0.01)


    def test_WHEN_phase_setpoint_is_set_THEN_actual_phase_gets_to_the_phase_just_set(self):
        for phase in TEST_PHASES:
            self.ca.set_pv_value("1:PHAS:SP", phase)
            self.ca.assert_that_pv_is_number("1:PHAS:SP", phase, 0.01)
            self.ca.assert_that_pv_is_number("1:PHAS", phase, 0.01)
