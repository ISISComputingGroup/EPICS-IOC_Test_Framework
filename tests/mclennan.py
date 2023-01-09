import unittest
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list
from parameterized import parameterized

DEVICE_PREFIX = "MCLEN_01"
EMULATOR_NAME = "mclennan"

MTR1 = "MTR0101"
MTR_DESC = f"{MTR1}.DESC"
MTR_JOG = f"{MTR1}.JOGF"
MTR_HLM = f"{MTR1}.HLM"
MTR_STOP = f"{MTR1}.STOP"
MTR_MOVN = f"{MTR1}.MOVN"
MTR_RBV = f"{MTR1}.RBV"
MTR_MRES = f"{MTR1}.MRES"
MTR2 = "MTR0102"
MTR2_MRES = f"{MTR2}.MRES"
MTR2_HVEL = f"{MTR2}.HVEL"
MTR2_HOMR = f"{MTR2}.HOMR"
MTR_NAME = "Test"

POLL_RATE = 1

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MCLEN"),
        "emulator": EMULATOR_NAME,
        "ioc_launcher_class": ProcServLauncher,
        "pv_for_existence": "AXIS1",
        "macros": {
            "MTRCTRL": "01",
            "AXIS1": "yes",
            "AXIS2": "yes",
            "NAME1": MTR_NAME,
            "POLL_RATE": POLL_RATE,
            "HOME2": 2
        },
    },
]


TEST_MODES = [
    TestModes.DEVSIM,
]


class MclennanTests(unittest.TestCase):
    """
    Tests for the Mclennan IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=10)
        self.ca_motor = ChannelAccess(default_timeout=30, device_prefix="MOT")
        self.ca_motor.set_pv_value(MTR_STOP, 1, sleep_after_set=0)

    def test_WHEN_ioc_running_THEN_motor_has_correct_description(self):
        self.ca_motor.assert_that_pv_is(MTR_DESC, MTR_NAME + " (MCLEN)")

    def test_WHEN_motor_jogged_THEN_motor_moves_and_does_not_stop_after_polled(self):
        self.ca_motor.assert_setting_setpoint_sets_readback(10000, MTR_HLM, set_point_pv=MTR_HLM)

        self.ca_motor.set_pv_value(MTR_JOG, 1, sleep_after_set=0)

        self.ca_motor.assert_that_pv_value_is_increasing(MTR_RBV, 1)
        self.ca_motor.assert_that_pv_is(MTR_MOVN, 1)
        self.ca_motor.assert_that_pv_value_is_unchanged(MTR_MOVN, POLL_RATE * 1.5)

    def test_WHEN_motor_position_changes_outside_IBEX_THEN_motor_position_updated(self):
        test_position = -10
        self.ca_motor.assert_that_pv_is_not_number(MTR_RBV, test_position)
        mres = self.ca_motor.get_pv_value(MTR_MRES)
        self._lewis.backdoor_set_on_device("position", test_position/mres)
        self.ca_motor.assert_that_pv_is_number(MTR_RBV, test_position)

    def test_WHEN_velocity_changes_WHEN_sending_home_THEN_velocity_is_changed_then_set_back_after_home(self):
        vel = 0.2
        self.ca_motor.set_pv_value(MTR2_HVEL, vel)
        self.ca_motor.set_pv_value(MTR2_HOMR, 1)
        mres = self.ca_motor.get_pv_value(MTR2_MRES)
        self._lewis.assert_that_emulator_value_is("creep_speed", str(int(vel/mres)))
        self.ca_motor.set_pv_value(MTR2, 1)
        self._lewis.assert_that_emulator_value_is("creep_speed", str(700))

    def test_WHEN_sending_home_with_high_velocity_THEN_creep_speed_is_capped(self):
        vel = 100
        self.ca_motor.set_pv_value(MTR2_HVEL, vel)
        self.ca_motor.set_pv_value(MTR2_HOMR, 1)
        # Should be capped at the max creep speed (800)
        self._lewis.assert_that_emulator_value_is("creep_speed", str(800))
        self.ca_motor.set_pv_value(MTR2, 1)
        self._lewis.assert_that_emulator_value_is("creep_speed", str(700))
