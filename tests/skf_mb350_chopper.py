import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

# Device prefix
DEVICE_PREFIX = "SKFMB350_01"

TEST_FREQUENCIES = [0, 17, 258, 1000]
TEST_PHASES = [0, 258.65, 10000.765]
TEST_PERCENTAGES = [0, 17.3, 99.8, 100]
TEST_PHAS_ERR_WIDTHS = [0.0, 0.2, 66.6, 100.0]
TEST_ANGLES = [0, 2, 90, 355]

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

PARK_OPEN_POSITION = 123

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SKFMB350"),
        "macros": {
            "PARKPOS": str(1),
            "PARKOPEN": str(PARK_OPEN_POSITION),
        },
        "emulator": "skf_mb350_chopper",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class SkfMB350ChopperTests(unittest.TestCase):
    """
    Tests for the SKF MB350 Chopper IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("skf_mb350_chopper", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

        self.ca.assert_that_pv_exists("FREQ", timeout=30)

        # Wait for emulator to be connected, signified by "STAT:OK"
        self.ca.assert_that_pv_is("STAT:OK", "OK")

    def test_WHEN_frequency_is_set_THEN_actual_frequency_gets_to_the_frequency_just_set(self):
        for frequency in TEST_FREQUENCIES:
            self.ca.set_pv_value("FREQ:SP", frequency)
            self.ca.assert_that_pv_is_number("FREQ:SP", frequency, 0.01)
            self.ca.set_pv_value("START", 1)  # Actually start the chopper.
            self.ca.assert_that_pv_is_number("FREQ", frequency, 0.01)

    def test_WHEN_phase_setpoint_is_set_THEN_actual_phase_gets_to_the_phase_just_set(self):
        for phase in TEST_PHASES:
            self.ca.set_pv_value("PHAS:SP", phase)
            self.ca.assert_that_pv_is_number("PHAS:SP", phase, 0.1)
            self.ca.assert_that_pv_is_number("PHAS", phase, 0.1)

    def test_WHEN_phase_setpoint_is_set_THEN_phase_sp_rbv_gets_to_the_phase_just_set(self):
        for phase in TEST_PHASES:
            self.ca.set_pv_value("PHAS:SP", phase)
            self.ca.assert_that_pv_is_number("PHAS:SP", phase, 0.1)
            self.ca.assert_that_pv_is_number("PHAS:SP:RBV", phase, 0.1)

    @skip_if_recsim("Uses lewis backdoor command")
    def test_WHEN_phase_repeatability_is_set_via_backdoor_THEN_the_repeatability_pv_updates_with_the_same_value(
        self,
    ):
        for phas_err_width in TEST_PHAS_ERR_WIDTHS:
            self._lewis.backdoor_set_on_device("phase_repeatability", phas_err_width)
            self.ca.assert_that_pv_is_number("PHAS_ERR", phas_err_width, 0.01)

    def test_WHEN_phas_err_width_is_set_via_pv_THEN_phas_err_width_pv_updates(self):
        for phas_err_width in TEST_PHAS_ERR_WIDTHS:
            self.ca.set_pv_value("PHAS_ERR:SP", phas_err_width)
            self.ca.assert_that_pv_is_number("PHAS_ERR:SP", phas_err_width, 0.01)
            self.ca.assert_that_pv_is_number("PHAS_ERR", phas_err_width, 0.01)

    @skip_if_recsim("Uses lewis backdoor command")
    def test_WHEN_phase_percent_ok_is_set_via_backdoor_THEN_the_percent_ok_pv_updates_with_the_same_value(
        self,
    ):
        for percentage in TEST_PERCENTAGES:
            self._lewis.backdoor_set_on_device("phase_percent_ok", percentage)
            self.ca.assert_that_pv_is_number("PHAS:PERCENTOK", percentage, 0.01)

    @skip_if_recsim("Uses lewis backdoor command")
    def test_WHEN_interlock_states_are_set_THEN_the_interlock_pvs_reflect_the_state_that_was_just_set(
        self,
    ):
        def _set_and_assert_interlock_state(interlock, on):
            self._lewis.backdoor_command(
                ["device", "set_interlock_state", interlock, "True" if on else "False"]
            )
            self.ca.assert_that_pv_is("ILK:{}".format(interlock), "Active" if on else "Inactive")

        for interlock in INTERLOCKS:
            _set_and_assert_interlock_state(interlock, True)
            _set_and_assert_interlock_state(interlock, False)

    @skip_if_recsim("Depends on state which is not implemented in recsim")
    def test_WHEN_device_is_started_then_stopped_THEN_up_to_speed_pv_reflects_the_stopped_or_started_state(
        self,
    ):
        self.ca.set_pv_value("START", 1)
        self.ca.assert_that_pv_is("STAT:UP_TO_SPEED", "YES")
        self.ca.set_pv_value("STOP", 1)
        self.ca.assert_that_pv_is("STAT:UP_TO_SPEED", "NO")

    def test_WHEN_rotator_angle_is_set_via_pv_THEN_rotator_angle_pv_updates_with_the_angle_just_set(
        self,
    ):
        # Check initial angle was the park open position - i.e. it was sent at IOC startup
        # This is the only test that sets the rotator angle so run this here - it's the only place which guarantees
        # running this test before the value is overwritten
        self.ca.assert_that_pv_is_number("ANGLE:ROTATOR", PARK_OPEN_POSITION, 0.01)

        for angle in TEST_ANGLES:
            self.ca.set_pv_value("ANGLE:ROTATOR:SP", angle)
            self.ca.assert_that_pv_is_number("ANGLE:ROTATOR", angle, 0.01)
