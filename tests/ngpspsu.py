import unittest
from parameterized import parameterized
from hamcrest import assert_that, is_, equal_to

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


def reset_device():
    """Reset the sp2xx device"""
    lewis, ioc = get_running_lewis_and_ioc("ngpspsu", DEVICE_PREFIX)
    ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
    return lewis, ioc, ca


##############################################
#
#       Unit tests
#
##############################################

class NgpspsuVersionTests(unittest.TestCase):
    """
    Tests for the Ngpspsu IOC.
    """
    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_device()

    def test_that_WHEN_requested_we_THEN_get_the_version_and_firmware(self):
        # When:
        self.ca.process_pv("VERSION")

        # Then:
        self.ca.assert_that_pv_is("VERSION", "NGPS 100-50:0.9.01")


class NgpspsuStartTests(unittest.TestCase):
    """
    Tests for the Ngpspsu IOC.
    """
    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_device()

    def test_that_WHEN_started_THEN_the_device_turns_on(self):
        # When:
        _start_device(self.ca)

        # Then:
        check_device_status_is("On", self._lewis)


class NgpspsuStopTests(unittest.TestCase):
    """
    Tests for the Ngpspsu IOC.
    """
    def setUp(self):
        self._lewis, self._ioc, self.ca = reset_device()

    def test_that_WHEN_on_setup_THEN_the_device_is_off(self):
        # When/Then:
        status = self._lewis.backdoor_run_function_on_device("get_status_via_the_backdoor")[0]
        assert_that(status, is_(equal_to("Off")))

    def test_that_GIVEN_a_device_which_is_running_THEN_the_device_turns_off(self):
        # Given:
        _start_device(self.ca)
        check_device_status_is("On", self._lewis)

        # When
        _stop_device(self.ca)

        # Then:
        check_device_status_is("Off", self._lewis)

