import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

from parameterized import parameterized

DEVICE_PREFIX = "DH2000_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DH2000"),
        "macros": {},
        "emulator": "dh2000",
    },
]


TEST_MODES = [TestModes.DEVSIM, ]


class Dh2000Tests(unittest.TestCase):
    """
    Tests for the Dh2000 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("dh2000", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        self._lewis.backdoor_set_on_device("shutter_is_open", False)
        self._lewis.backdoor_set_on_device("interlock_is_triggered", False)

        self.ca.assert_that_pv_is("SHUTTER:STATUS", "CLOSED")
        self.ca.assert_that_pv_is("INTERLOCK", "OKAY")

    @parameterized.expand([
        ("shutter_open_interlock_off", True, False),
        ("shutter_closed_interlock_off", False, False),
        ("shutter_closed_interlock_on", False, True)
    ])
    def test_GIVEN_device_in_a_state_WHEN_status_requested_THEN_shutter_and_interlock_status_returned(self, _, shutter_is_open, interlock_is_triggered):
        # GIVEN
        self._lewis.backdoor_set_on_device("shutter_is_open", shutter_is_open)
        self._lewis.backdoor_set_on_device("interlock_is_triggered", interlock_is_triggered)

        # THEN
        self.ca.assert_that_pv_is("INTERLOCK", "TRIGGERED" if interlock_is_triggered else "OKAY")
        self.ca.assert_that_pv_is("SHUTTER:STATUS", "OPEN" if shutter_is_open else "CLOSED")

    def test_GIVEN_shutter_open_WHEN_interlock_triggered_THEN_shutter_closes(self):
        self._lewis.backdoor_set_on_device("shutter_is_open", True)
        self._lewis.backdoor_set_on_device("interlock_is_triggered", False)

        # GIVEN
        self.ca.assert_that_pv_is("SHUTTER:STATUS", "OPEN")
        self.ca.assert_that_pv_is("INTERLOCK", "OKAY")

        # WHEN
        self._lewis.backdoor_set_on_device("interlock_is_triggered", True)

        # THEN
        self.ca.assert_that_pv_is("INTERLOCK", "TRIGGERED")
        self.ca.assert_that_pv_is("SHUTTER:STATUS", "CLOSED")

    def test_GIVEN_shutter_open_WHEN_shutter_close_requested_THEN_shutter_closes(self):
        # GIVEN
        self._lewis.backdoor_set_on_device("shutter_is_open", True)
        self.ca.assert_that_pv_is("SHUTTER:STATUS", "OPEN")

        # WHEN
        self.ca.process_pv("SHUTTER:CLOSE")

        # THEN
        self.ca.assert_that_pv_is("SHUTTER:STATUS", "CLOSED")

    def test_GIVEN_shutter_closed_and_interlock_not_triggered_WHEN_shutter_open_requested_THEN_shutter_opens(self):
        # GIVEN
        self.ca.assert_that_pv_is("INTERLOCK", "OKAY")
        self.ca.assert_that_pv_is("SHUTTER:STATUS", "CLOSED")

        # WHEN
        self.ca.process_pv("SHUTTER:OPEN")

        # THEN
        self.ca.assert_that_pv_is("SHUTTER:STATUS", "OPEN")

    def test_GIVEN_shutter_closed_and_interlock_triggered_WHEN_shutter_open_requested_THEN_shutter_does_not_open(self):
        # GIVEN
        self._lewis.backdoor_set_on_device("interlock_is_triggered", True)
        self.ca.assert_that_pv_is("INTERLOCK", "TRIGGERED")
        self.ca.assert_that_pv_is("SHUTTER:STATUS", "CLOSED")

        # WHEN
        self.ca.process_pv("SHUTTER:OPEN")

        # THEN
        self.ca.assert_that_pv_is("SHUTTER:STATUS", "CLOSED")

    def test_GIVEN_interlock_triggered_THEN_interlock_PV_has_major_alarm(self):
        # GIVEN
        self._lewis.backdoor_set_on_device("interlock_is_triggered", True)

        self.ca.assert_that_pv_alarm_is("INTERLOCK", self.ca.Alarms.MAJOR)
