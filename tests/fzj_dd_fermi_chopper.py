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
    Tests for the FZJ Digital Drive Fermi Chopper Controller
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("fzj_dd_fermi_chopper")

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        # self._lewis.backdoor_set_on_device("address", ADDRESS)

    def _set_state(self, expected_state):
        self._lewis.backdoor_set_on_device("magnetic_bearing_status", expected_state)
        self._ioc.set_simulated_value("SIM:MB:STATUS", expected_state)

    def test_GIVEN_magnetic_bearings_state_WHEN_read_THEN_state_is_as_expected(self):
        expected_state = "ON"
        self._set_state(expected_state)

        self.ca.assert_that_pv_is("MB:STATUS", expected_state)
        self.ca.assert_pv_alarm_is("MB:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_reference_frequency_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 50
        self._set_all_status(reference_frequency=expected_value)

        self.ca.assert_that_pv_is("FREQ:REF", expected_value)
        self.ca.assert_pv_alarm_is("FREQ:REF", ChannelAccess.ALARM_NONE)

    def test_GIVEN_frequency_setpoint_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 60
        self._set_all_status(frequency_setpoint=expected_value)

        self.ca.assert_that_pv_is("FREQ:SP:RBV", expected_value)
        self.ca.assert_pv_alarm_is("FREQ:SP:RBV", ChannelAccess.ALARM_NONE)

    def test_GIVEN_frequency_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 35
        self._set_all_status(frequency=expected_value)

        self.ca.assert_that_pv_is("FREQ", expected_value)
        self.ca.assert_pv_alarm_is("FREQ", ChannelAccess.ALARM_NONE)

    def _set_all_status(self, reference_frequency=10, frequency_setpoint=10, frequency=10):
        self._lewis.backdoor_set_on_device("reference_frequency", reference_frequency)
        self._lewis.backdoor_set_on_device("frequency_setpoint", frequency_setpoint)
        self._lewis.backdoor_set_on_device("frequency", frequency)

        self._ioc.set_simulated_value("SIM:FREQ:REF", reference_frequency)
        self._ioc.set_simulated_value("SIM:FREQ:SP:RBV", frequency_setpoint)
        self._ioc.set_simulated_value("SIM:FREQ", frequency)
