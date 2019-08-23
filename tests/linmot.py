import unittest
from time import sleep

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
        self._lewis.backdoor_run_function_on_device("reset")
        self.ca_linmot.assert_that_pv_exists("MTR0101.RBV")

    @skip_if_recsim("Lewis backdoor not available in RECSIM mode")
    def test_GIVEN_motor_destination_WHEN_motor_given_destination_THEN_move_to_correct_place(self):
        expected_value = 90
        # this gives the computer the set point
        self.ca_linmot.set_pv_value("MTR0101.VAL", expected_value)
        # this shows what the readback value was (it should be the same as the setpoint
        self.ca_linmot.assert_that_pv_is("MTR0101.RBV", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_device_not_connected_WHEN_get_error_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca_linmot.set_pv_value("MTR0101.VAL", 1)
        self.ca_linmot.assert_that_pv_alarm_is('MTR0101', ChannelAccess.Alarms.INVALID, timeout=5)

    @skip_if_recsim("Lewis backdoor not available in RECSIM mode")
    def test_GIVEN_velocity_WHEN_started_up_THEN_velocity_is_correct(self):
        expected_value = "1"
        self.ca_linmot.set_pv_value("MTR0101.VELO", expected_value)
        self.ca_linmot.set_pv_value("MTR0101.VAL", 10)
        device_value = self._lewis.backdoor_get_from_device("velocity")

        self.assertEqual(expected_value, device_value)

    @skip_if_recsim("Lewis backdoor not available in RECSIM mode")
    def test_GIVEN_start_up_WHEN_get_motor_warn_status_THEN_it_is_correct(self):
        sleep(5)
        expected_value = "256"
        device_value = self._lewis.backdoor_get_from_device("motor_warn_status")
        self.assertEqual(device_value, expected_value)

    def test_GIVEN_new_accel_WHEN_set_accel_THEN_accel_set(self):
        expected_value = 2
        self.ca_linmot.set_pv_value("MTR0101.ACCL", expected_value)
        self.ca_linmot.assert_that_pv_is("MTR0101.ACCL", expected_value)

    @skip_if_recsim("Lewis backdoor not available in RECSIM mode")
    def test_GIVEN_new_position_WHEN_moving_THEN_DMOVE_status_updated(self):
        expected_value = 0
        self.ca_linmot.set_pv_value("MTR0101:SP", 9000)
        self.ca_linmot.assert_that_pv_is("MTR0101.DMOV", expected_value)
