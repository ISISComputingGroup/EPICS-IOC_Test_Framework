import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

MACROS = {"MTRCTRL": "01", "AXIS1": "yes"}


class Sm300Tests(unittest.TestCase):
    """
    Tests for the Samsm300 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("sm300")
        self.ca = ChannelAccess(device_prefix="MOT")

    def test_that_fails(self):
        expected_value = 100
        self._lewis.backdoor_set_on_device("x_axis_rbv", expected_value)
        self._lewis.backdoor_set_on_device("x_axis_sp", expected_value)


        self.ca.assert_that_pv_is("MTR0101.RBV", expected_value)
