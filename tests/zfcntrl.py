import contextlib
import unittest
from enum import Enum

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list

DEVICE_PREFIX = "ZFCNTRL_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ZFCNTRL"),
        "started_text": "seq zero_field",
    },
]


TEST_MODES = [TestModes.RECSIM]

FIELD_AXES = ["X", "Y", "Z"]


class Statuses(object):
    NO_ERROR = ("No error", ChannelAccess.Alarms.NONE)
    MAGNETOMETER_READ_ERROR = ("Magnetometer read error", ChannelAccess.Alarms.MAJOR)
    MAGNETOMETER_OVERLOAD = ("Magnetometer overloaded", ChannelAccess.Alarms.MAJOR)


class ZeroFieldTests(unittest.TestCase):
    """
    Tests for the muon zero field controller IOC.
    """
    def _set_simulated_fields(self, x, y, z, overload=False, set_setpoints=False):
        self.ca.set_pv_value("SIM:MAGNETOMETER:X", x, sleep_after_set=0)
        self.ca.set_pv_value("SIM:MAGNETOMETER:Y", y, sleep_after_set=0)
        self.ca.set_pv_value("SIM:MAGNETOMETER:Z", z, sleep_after_set=0)

        self.ca.set_pv_value("SIM:MAGNETOMETER:OVERLOAD", "Out of range" if overload else "In range", sleep_after_set=0)

        if set_setpoints:
            self._change_setpoints(x, y, z)

    def _change_setpoints(self, x, y, z):
        self.ca.set_pv_value("FIELD:X:SP", x, sleep_after_set=0)
        self.ca.set_pv_value("FIELD:Y:SP", y, sleep_after_set=0)
        self.ca.set_pv_value("FIELD:Z:SP", z, sleep_after_set=0)

    def _assert_stable(self, stable):
        self.ca.assert_that_pv_is("STABLE", "Stable" if stable else "Unstable")
        self.ca.assert_that_pv_alarm_is("STABLE", self.ca.Alarms.NONE if stable else self.ca.Alarms.MAJOR)

    def _assert_status(self, status):
        self.ca.assert_that_pv_is("STATUS", status[0])
        self.ca.assert_that_pv_alarm_is("STATUS", status[1])

    @contextlib.contextmanager
    def _simulate_disconnected_magnetometer(self):
        self.ca.set_pv_value("SIM:MAGNETOMETER_DISCONNECTED", 1, sleep_after_set=0)
        try:
            yield
        finally:
            self.ca.set_pv_value("SIM:MAGNETOMETER_DISCONNECTED", 0, sleep_after_set=0)

    def setUp(self):
        _, self._ioc = get_running_lewis_and_ioc(None, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=20)
        self.ca.assert_that_pv_exists("DISABLE")
        self.ca.set_pv_value("TOLERANCE", 1, sleep_after_set=0)

        self._set_simulated_fields(0, 0, 0, overload=False, set_setpoints=True)
        self._assert_stable(True)
        self._assert_status(Statuses.NO_ERROR)

    def test_WHEN_ioc_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(FIELD_AXES))
    def test_WHEN_any_readback_value_is_not_equal_to_setpoint_THEN_field_is_marked_as_unstable(self, _, axis_to_vary):
        self._set_simulated_fields(10, 20, 30, set_setpoints=True, overload=False)

        # Set one of the parameters to a completely different value
        self.ca.set_pv_value("FIELD:{}:SP".format(axis_to_vary), 100, sleep_after_set=0)

        self._assert_stable(False)
        self._assert_status(Statuses.NO_ERROR)

    def test_GIVEN_magnetometer_not_overloaded_WHEN_readback_values_are_equal_to_setpoints_THEN_field_is_marked_as_stable(self):
        self._set_simulated_fields(55, 66, 77, set_setpoints=True, overload=False)

        self._assert_stable(True)
        self._assert_status(Statuses.NO_ERROR)

    def test_GIVEN_within_tolerance_WHEN_magnetometer_is_overloaded_THEN_status_overloaded_and_stable(self):
        self._set_simulated_fields(55, 66, 77, overload=True, set_setpoints=True)

        self._assert_stable(True)
        self._assert_status(Statuses.MAGNETOMETER_OVERLOAD)

    def test_GIVEN_outside_tolerance_WHEN_magnetometer_is_overloaded_THEN_status_overloaded_and_unstable(self):
        self._set_simulated_fields(55, 66, 77, overload=True)
        self._change_setpoints(66, 77, 88)

        self._assert_stable(False)
        self._assert_status(Statuses.MAGNETOMETER_OVERLOAD)

    def test_WHEN_magnetometer_ioc_does_not_respond_THEN_status_is_magnetometer_read_error(self):
        self._set_simulated_fields(1, 2, 3, overload=False, set_setpoints=True)

        with self._simulate_disconnected_magnetometer():
            self._assert_stable(False)
            self._assert_status(Statuses.MAGNETOMETER_READ_ERROR)

        # Now simulate recovery and assert error gets cleared correctly
        self._assert_stable(True)
        self._assert_status(Statuses.NO_ERROR)
