import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister, EPICS_TOP, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import parameterized_list
import os
from genie_python import genie as g
from parameterized import parameterized
import time
from contextlib import contextmanager


IOC_PREFIX = "TIZR_01"
DEVICE_PREFIX = g.my_pv_prefix
SIMPLE_VALUE_ONE = "SIMPLE:VALUE1:SP"
SIMPLE_VALUE_TWO = "SIMPLE:VALUE2"

# Values chosen to be within high range of simple PVs
PVONE_MAX = 12
IN_RANGE_PVONE_VAL = 0.5 * PVONE_MAX
OUT_OF_RANGE_PVONE_VAL = 2.0*PVONE_MAX
PVTWO_MAX = 8
IN_RANGE_PVTWO_VAL = 0.5 * PVTWO_MAX
OUT_OF_RANGE_PVTWO_VAL = 2.0*PVTWO_MAX
SAFE_VALUE = 11

tizr_macros = {
    "PVONE": "{prefix}{pv}".format(prefix=DEVICE_PREFIX, pv=SIMPLE_VALUE_ONE),
    "PVTWO": "{prefix}{pv}".format(prefix=DEVICE_PREFIX, pv=SIMPLE_VALUE_TWO),
    "PVONE_MAX": PVONE_MAX,
    "PVTWO_MAX": PVTWO_MAX,
    "SAFE_VALUE": SAFE_VALUE
}


IOCS = [
    {
        "name": IOC_PREFIX,
        "directory": get_default_ioc_dir("TIZR"),
        "macros": tizr_macros,
        "ioc_launcher_class": ProcServLauncher,
        "pv_for_existence": "TIZRWARNING",
    },
    {
        "name": "SIMPLE",
        "directory": os.path.join(EPICS_TOP, "ISIS", "SimpleIoc", "master", "iocBoot", "iocsimple"),
        "macros": {},
    }
]

WARNING_PV = "{}:TIZRWARNING".format(IOC_PREFIX)
MONITORING_ON_PV = "{}:MONITORING_ON".format(IOC_PREFIX)

TEST_MODES = [TestModes.RECSIM]


class TiZrTests(unittest.TestCase):
    """
    Tests for the TiZr cell monitoring logic.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(IOC_PREFIX)
        self.ca = ChannelAccess(default_timeout=20)

        for pv in [SIMPLE_VALUE_ONE, SIMPLE_VALUE_TWO]:
            self.ca.assert_that_pv_exists(pv)

        self.set_safe_values()
        self.ca.set_pv_value(MONITORING_ON_PV, "No")
        self.ca.assert_that_pv_is(MONITORING_ON_PV, "No")

    @contextmanager
    def monitoring_on(self):
        try:
            self.ca.set_pv_value(MONITORING_ON_PV, "Yes")
            self.ca.assert_that_pv_is(MONITORING_ON_PV, "Yes")
            yield
        finally:
            self.ca.set_pv_value(MONITORING_ON_PV, "No")
            self.ca.assert_that_pv_is(MONITORING_ON_PV, "No")

    def set_safe_values(self):
        self.ca.set_pv_value(SIMPLE_VALUE_ONE, IN_RANGE_PVONE_VAL)
        self.ca.set_pv_value(SIMPLE_VALUE_TWO, IN_RANGE_PVTWO_VAL)
        self.ca.set_pv_value(WARNING_PV, 0)

    def test_GIVEN_monitor_on_AND_PVONE_above_max_WHEN_PVTWO_goes_out_of_range_THEN_alarm_and_safe_value_written_to_PVONE(self):
        with self.monitoring_on():
            self.ca.set_pv_value(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL)
            self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL, tolerance=1e-4)

            self.ca.set_pv_value(SIMPLE_VALUE_TWO, OUT_OF_RANGE_PVTWO_VAL)

            self.ca.assert_that_pv_is_not_number(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL, tolerance=1e-4)
            self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, SAFE_VALUE, tolerance=1e-4)

            self.ca.assert_that_pv_alarm_is(WARNING_PV, self.ca.Alarms.MAJOR)

    def test_GIVEN_monitor_off_AND_PVONE_above_max_WHEN_PVTWO_goes_out_of_range_THEN_no_alarm_and_no_safe_value_written_to_PVONE(self):
        self.ca.set_pv_value(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL)
        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL, tolerance=1e-4)

        self.ca.set_pv_value(SIMPLE_VALUE_TWO, OUT_OF_RANGE_PVTWO_VAL)

        self.ca.assert_that_pv_is_not_number(SIMPLE_VALUE_ONE, SAFE_VALUE, tolerance=1e-4)
        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL, tolerance=1e-4)

        self.ca.assert_that_pv_alarm_is_not(WARNING_PV, self.ca.Alarms.MAJOR)

    def test_GIVEN_monitor_on_AND_PVTWO_above_max_WHEN_PVONE_out_of_range_THEN_alarm_and_safe_value_written_to_PVONE(self):
        with self.monitoring_on():
            self.ca.set_pv_value(SIMPLE_VALUE_TWO, OUT_OF_RANGE_PVTWO_VAL)
            self.ca.assert_that_pv_is_number(SIMPLE_VALUE_TWO, OUT_OF_RANGE_PVTWO_VAL, tolerance=1e-4)

            self.ca.set_pv_value(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL)

            self.ca.assert_that_pv_alarm_is(WARNING_PV, self.ca.Alarms.MAJOR)

            self.ca.assert_that_pv_is_not_number(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL, tolerance=1e-4)
            self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, SAFE_VALUE, tolerance=1e-4)

    def test_GIVEN_monitor_off_AND_PVTWO_above_max_WHEN_PVONE_out_of_range_THEN_no_alarm_and_no_safe_value_written_to_PVONE(self):
        self.ca.set_pv_value(SIMPLE_VALUE_TWO, OUT_OF_RANGE_PVTWO_VAL)
        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_TWO, OUT_OF_RANGE_PVTWO_VAL, tolerance=1e-4)

        self.ca.set_pv_value(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL)

        self.ca.assert_that_pv_alarm_is_not(WARNING_PV, self.ca.Alarms.MAJOR)

        self.ca.assert_that_pv_is_not_number(SIMPLE_VALUE_ONE, SAFE_VALUE, tolerance=1e-4)
        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL, tolerance=1e-4)

    def test_GIVEN_monitor_on_AND_PVONE_and_PVTWO_in_range_WHEN_in_range_value_written_THEN_no_alarm_and_value_written(self):
        with self.monitoring_on():
            self.ca.set_pv_value(SIMPLE_VALUE_ONE, IN_RANGE_PVONE_VAL)
            self.ca.set_pv_value(SIMPLE_VALUE_TWO, IN_RANGE_PVTWO_VAL)

            self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, IN_RANGE_PVONE_VAL)
            self.ca.assert_that_pv_is_number(SIMPLE_VALUE_TWO, IN_RANGE_PVTWO_VAL)

            self.ca.assert_that_pv_alarm_is(WARNING_PV, self.ca.Alarms.NONE)

            self.ca.assert_that_pv_alarm_is(SIMPLE_VALUE_ONE, self.ca.Alarms.NONE)
            self.ca.assert_that_pv_alarm_is(SIMPLE_VALUE_TWO, self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list([
        (SIMPLE_VALUE_ONE, IN_RANGE_PVONE_VAL), (SIMPLE_VALUE_TWO, IN_RANGE_PVTWO_VAL)
    ]))
    def test_GIVEN_monitor_on_AND_pvs_in_range_WHEN_one_goes_out_of_range_THEN_no_alarm_and_value_written(self, _, pv, in_range_value):
        with self.monitoring_on():
            self.ca.set_pv_value(pv, in_range_value)
            self.ca.assert_that_pv_is_number(pv, in_range_value)
            self.ca.assert_that_pv_alarm_is(WARNING_PV, self.ca.Alarms.NONE)
            self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)

    def test_GIVEN_monitor_on_AND_safe_value_is_out_of_range_WHEN_safe_value_set_THEN_alarm_persisted(self):
        macros = tizr_macros
        macros["SAFE_VALUE"] = OUT_OF_RANGE_PVONE_VAL
        macros["MONITORING_ON"] = "1"
        with self._ioc.start_with_macros(macros, "TIZRWARNING"):
            self.ca.assert_that_pv_is(MONITORING_ON_PV, "Yes")
            self.ca.set_pv_value(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL)
            self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, OUT_OF_RANGE_PVONE_VAL, tolerance=1e-4)

            self.ca.set_pv_value(SIMPLE_VALUE_TWO, OUT_OF_RANGE_PVTWO_VAL)
            self.ca.assert_that_pv_is_number(SIMPLE_VALUE_TWO, OUT_OF_RANGE_PVTWO_VAL, tolerance=1e-4)

            self.ca.assert_that_pv_alarm_is(WARNING_PV, self.ca.Alarms.MAJOR)
            time.sleep(10)
            self.ca.assert_that_pv_alarm_is(WARNING_PV, self.ca.Alarms.MAJOR)
