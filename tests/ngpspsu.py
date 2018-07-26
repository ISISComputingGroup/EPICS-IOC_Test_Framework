import unittest
from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "NGPSPSU_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("NGPSPSU"),
        "macros": {},
        "emulator": "ngpspsu",
    },
]


TEST_MODES = [TestModes.DEVSIM] #, TestModes.RECSIM]

##############################################
#
#       Useful functions to run tests
#
##############################################


def reset_emulator():
    """Reset the sp2xx device"""
    lewis, ioc = get_running_lewis_and_ioc("ngpspsu", DEVICE_PREFIX)
    ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

    _reset_error(ca)
    ca.assert_that_pv_is("ERROR", "0")

    _stop_device(ca)
    ca.assert_that_pv_is("STAT:ON_OFF", "OFF")

    return lewis, ioc, ca


def _stop_device(ca):
    ca.set_pv_value("ON_OFF:SP", 0)


def _start_device(ca):
    ca.set_pv_value("ON_OFF:SP", 1)


def _reset_error(ca):
    ca.set_pv_value("ERROR", "0")


def _reset_device(ca):
    ca.process_pv("RESET:SP")

##############################################
#
#       Unit tests
#
##############################################


class NgpspsuVersionTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def test_that_WHEN_requested_we_THEN_get_the_version_and_firmware(self):
        # When:
        self.ca.process_pv("VERSION")

        # Then:
        self.ca.assert_that_pv_is("VERSION", "NGPS 100-50:0.9.01")


class NgpspsuStartAndStopTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def test_that_WHEN_started_THEN_the_device_turns_on(self):
        # When:
        _start_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("STAT:ON_OFF", "ON")

    def test_that_GIVEN_a_fresh_device_THEN_the_device_is_off(self):
        # When/Then:
        self.ca.assert_that_pv_is("STAT:ON_OFF", "OFF")

    def test_that_GIVEN_a_device_which_is_running_THEN_the_device_turns_off(self):
        # Given:
        _start_device(self.ca)
        self.ca.assert_that_pv_is("STAT:ON_OFF", "ON")

        # When
        _stop_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("STAT:ON_OFF", "OFF")


class NgpspsuStatusTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def test_that_GIVEN_a_setup_device_THEN_the_status_is_zero(self):
        # When/Then:
        for digit in range(1, 9):
            self.ca.assert_that_pv_is("STAT:HEX:{}".format(digit), 0)


class NgpspsuErrorTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def test_that_GIVEN_a_setup_device_THEN_there_is_no_error_state(self):
        # When/Then:
        self.ca.assert_that_pv_is("ERROR", "0")

    def test_that_GIVEN_a_running_device_WHEN_making_it_run_THEN_there_is_no_error_state(self):
        # Given
        _start_device(self.ca)

        # When
        _start_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("ERROR", "0")

    def test_that_GIVEN_a_stopped_device_WHEN_making_it_stop_THEN_there_is_no_error_state(self):
        # Given
        _stop_device(self.ca)

        # When
        _stop_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("ERROR", "0")


class NgpspsuResetTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def test_that_GIVEN_a_running_device_WHEN_reset_THEN_the_device_stops(self):
        # Given
        _start_device(self.ca)

        # When
        _reset_device(self.ca)

        # Then:
        self.ca.assert_that_pv_is("ERROR", "0")


class NgpspsuVoltageTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_emulator()

    def test_that_GIVEN_a_device_after_set_up_THEN_the_voltage_is_zero(self):
        # Then:
        self.ca.assert_that_pv_is("VOLT", 0.0)

