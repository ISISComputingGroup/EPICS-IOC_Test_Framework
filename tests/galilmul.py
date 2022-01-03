import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes

DEVICE_PREFIX = "GALILMUL_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("GALILMUL"),
        "pv_for_existence": "1:AXIS1",
        "macros": {
            "MTRCTRL1": "01",
            "GALILADDR1": "127.0.0.11,
            "MTRCTRL2": "02",
            "GALILADDR2": "127.0.0.12",
        },
    },
]

TEST_MODES = [TestModes.DEVSIM]


class GalilmulTests(unittest.TestCase):
    """
    Tests for loading multiple motor controllers into a single IOC
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=None, default_timeout=20)

    def test_GIVEN_ioc_started_THEN_pvs_for_all_motors_exist(self):
        for controller in ("01", "02"):
            for motor in ["{:02d}".format(mtr) for mtr in range(1, 8 + 1)]:
                self.ca.assert_that_pv_exists("MOT:MTR{}{}".format(controller, motor))

    def test_GIVEN_ioc_started_THEN_axes_for_all_motors_exist(self):
        for controller in (1, 2):
            for motor in range(1, 8 + 1):
                self.ca.assert_that_pv_exists("GALILMUL_01:{}:AXIS{}".format(controller, motor))

    def test_GIVEN_axis_moved_THEN_other_axes_do_not_move(self):
        # This is to check that axes are independent, i.e. they're not accidentally using the same underlying driver

        # Set all motors to zero
        for controller in ("01", "02"):
            for motor in ["{:02d}".format(mtr) for mtr in range(1, 8 + 1)]:
                self.ca.set_pv_value("MOT:MTR{}{}".format(controller, motor), 0)
                self.ca.assert_that_pv_is("MOT:MTR{}{}".format(controller, motor), 0)

        # Move motor 0101
        self.ca.set_pv_value("MOT:MTR0101", 20)
        self.ca.assert_that_pv_is("MOT:MTR0101", 20)

        # Check all other motors are still at zero
        for controller in ("01", "02"):
            for motor in ["{:02d}".format(mtr) for mtr in range(1, 8 + 1)]:
                if controller == "01" and motor == "01":
                    continue
                self.ca.assert_that_pv_is("MOT:MTR{}{}".format(controller, motor), 0)
