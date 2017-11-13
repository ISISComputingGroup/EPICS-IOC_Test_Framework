import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

# MACROS to use for the IOC
MACROS = {}

# Device prefix
DEVICE_PREFIX = "FZJDDFCH_01"


class Fzj_dd_fermi_chopperTests(unittest.TestCase):
    """
    Tests for the 
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("fzj_dd_fermi_chopper")

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        # self._lewis.backdoor_set_on_device("address", ADDRESS)

    def _set_state(self, expected_state):
        self._lewis.backdoor_set_on_device("magnetic_bearing_state", expected_state)
        self._ioc.set_simulated_value("SIM:MB:STATE", expected_state)

    def test_GIVEN_magnetic_bearings_state_WHEN_read_THEN_state_is_as_expected(self):
        expected_state = "ON"
        self._set_state(expected_state)

        self.ca.assert_that_pv_is("MB:STATE", expected_state)
        self.ca.assert_pv_alarm_is("MB:STATE", ChannelAccess.ALARM_NONE)
