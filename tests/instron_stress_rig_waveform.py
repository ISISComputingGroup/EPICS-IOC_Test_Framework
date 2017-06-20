import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

import math


class Instron_stress_rigTests(unittest.TestCase):
    """
    Tests for the Instron IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("instron_stress_rig")

        self.ca = ChannelAccess(15)
        self.ca.wait_for("INSTRON_01:CHANNEL", timeout=30)

    def test_WHEN_the_rig_is_in_its_initial_state_THEN_the_waveform_generator_is_stopped(self):
        self.ca.assert_that_pv_is("INSTRON_01:WAVE:STATUS", "Stopped")

    def test_WHEN_the_rig_is_in_its_initial_state_THEN_the_waveform_generator_is_not_running(self):
        self.ca.assert_that_pv_is("INSTRON_01:WAVE:RUNNING", "Not running")

    def test_WHEN_the_rig_is_in_its_initial_state_THEN_the_waveform_generator_is_not_continuing(self):
        self.ca.assert_that_pv_is("INSTRON_01:WAVE:RUNNING", "Not continuing")
