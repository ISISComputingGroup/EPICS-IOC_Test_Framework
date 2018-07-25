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

    def test_that_WHEN_started_THEN_the_device_is_on(self):
        # When:
        self.ca.set_pv_value("ON:SP", 1)

        # Then:
        status = self._lewis.backdoor_run_function_on_device("get_status_via_the_backdoor")[0]
        assert_that(status, is_(equal_to("On")))
