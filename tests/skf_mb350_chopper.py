import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "SKFMB350_01"

TEST_FREQUENCIES = [0, 17, 258, 10000]
TEST_PHASES = [0, 17.3, 258.65, 10000.765]
TEST_PERCENTAGES = [0.0, 0.2, 66.6, 100.0]

INTERLOCKS = [
    "DSP_WD_FAIL",
    "OSCILLATOR_FAIL",
    "POSITION_SHUTDOWN",
    "EMERGENCY_STOP",
    "UPS_FAIL",
    "EXTERNAL_FAULT",
    "CC_WD_FAIL",
    "OVERSPEED_TRIP",
    "VACUUM_FAIL",
    "MOTOR_OVER_TEMP",
    "REFERENCE_SIGNAL_LOSS",
    "SPEED_SENSOR_LOSS",
    "COOLING_LOSS",
    "DSP_SUMMARY_SHUTDOWN",
    "CC_SHUTDOWN_REQ",
    "TEST_MODE",
]

STATUSES = [
    "OK",
    "UP_TO_SPEED",
    "RUN",
    "SHUTDOWN",
    "LEVITATION_COMPLETE",
    "PHASE_LOCKED",
    "DIRECTION",
    "AVC_ON",
]


class Skf_mb350_chopperTests(unittest.TestCase):
    """
    Tests for the SKF MB350 Chopper IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("skf_mb350_chopper")
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

        self.ca.wait_for("FREQ", timeout=30)

    def test_WHEN_frequency_is_set_THEN_actual_frequency_gets_to_the_frequency_just_set(self):
        for frequency in TEST_FREQUENCIES:
            self.ca.set_pv_value("FREQ:SP", frequency)
            self.ca.assert_that_pv_is_number("FREQ:SP", frequency, 0.01)
            self.ca.assert_that_pv_is_number("FREQ", frequency, 0.01)

    def test_WHEN_phase_setpoint_is_set_THEN_actual_phase_gets_to_the_phase_just_set(self):
        for phase in TEST_PHASES:
            self.ca.set_pv_value("PHAS:SP", phase * 1000)
            self.ca.assert_that_pv_is_number("PHAS:SP", phase*1000, 0.01)
            self.ca.assert_that_pv_is_number("PHAS", phase, 0.01)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_phase_repeatability_is_set_via_backdoor_THEN_the_repeatability_pv_updates_with_the_same_value(self):
        for percentage in TEST_PERCENTAGES:
            self._lewis.backdoor_set_on_device("phase_repeatability", percentage)
            self.ca.assert_that_pv_is_number("PHAS:REPEATABILITY", percentage, 0.01)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_phase_percent_ok_is_set_via_backdoor_THEN_the_percent_ok_pv_updates_with_the_same_value(self):
        for percentage in TEST_PERCENTAGES:
            self._lewis.backdoor_set_on_device("phase_percent_ok", percentage)
            self.ca.assert_that_pv_is_number("PHAS:PERCENTOK", percentage, 0.01)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_interlock_states_are_set_THEN_the_interlock_pvs_reflect_the_state_that_was_just_set(self):

        def _set_and_assert_interlock_state(interlock, on):
            self._lewis.backdoor_command(["device", "set_interlock_state", interlock, "True" if on else "False"])
            self.ca.assert_that_pv_is("STAT:ILK:{}".format(interlock), "Active" if on else "Inactive")

        for interlock in INTERLOCKS:
            _set_and_assert_interlock_state(interlock, True)

    def test_device_stopped(self):
        self.ca.assert_that_pv_is("STAT:OK", "OK")
