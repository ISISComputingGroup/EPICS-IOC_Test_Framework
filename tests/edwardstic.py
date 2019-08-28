import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

from parameterized import parameterized

DEVICE_PREFIX = "EDTIC_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("EDTIC"),
        "macros": {},
        "emulator": "edwardstic",
    },
]

# No recsim as this device makes heavy use of record redirection
TEST_MODES = [TestModes.DEVSIM, ]


class EdwardsTICTests(unittest.TestCase):
    """
    Tests for the Edwards Turbo Instrument Controller (TIC) IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("edwardstic", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device("is_connected", True)

        self.ca.assert_setting_setpoint_sets_readback("No", "TURBO:STBY", set_point_pv="TURBO:SETSTBY", timeout=30)

    def test_GIVEN_turbo_pump_switched_on_WHEN_status_requested_THEN_status_reads_switched_on(self):
        # GIVEN
        self.ca.set_pv_value("TURBO:START", "On", wait=True)

        # THEN
        self.ca.assert_that_pv_is("TURBO:STA", "Running")

    def test_GIVEN_standby_mode_switched_on_WHEN_status_requested_THEN_standby_reads_switched_on(self):
        # GIVEN
        self.ca.set_pv_value("TURBO:SETSTBY", "Yes", wait=True)

        # THEN
        self.ca.assert_that_pv_is("TURBO:STBY", "Yes")

    def test_GIVEN_standby_mode_switched_off_WHEN_status_requested_THEN_standby_reads_switched_off(self):
        # GIVEN
        self.ca.set_pv_value("TURBO:SETSTBY", "No", wait=True)

        # THEN
        self.ca.assert_that_pv_is("TURBO:STBY", "No")

    @parameterized.expand([
        ("turbo_status", "TURBO:STA"),
        ("turbo_speed", "TURBO:SPEED"),
        ("turbo_power", "TURBO:POWER"),
        ("turbo_norm", "TURBO:NORM"),
        ("turbo_standby", "TURBO:STBY"),
        ("turbo_cycle", "TURBO:CYCLE")
    ])
    def test_GIVEN_disconnected_device_WHEN_pump_status_read_THEN_PVs_read_invalid(self, _, base_pv):
        # GIVEN
        self._lewis.backdoor_set_on_device("is_connected", False)

        # WHEN
        self.ca.assert_that_pv_alarm_is(base_pv, self.ca.Alarms.INVALID, timeout=20)
        self.ca.assert_that_pv_alarm_is("{base}:ALERT".format(base=base_pv), self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is("{base}:PRI".format(base=base_pv), self.ca.Alarms.INVALID)
