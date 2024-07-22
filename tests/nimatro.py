import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, ProcServLauncher, get_default_ioc_dir
from utils.test_modes import TestModes

DEVICE_PREFIX = "NIMATRO_01"
AREA_DEFAULT_HIGH_LIMIT = 247
AREA_DEFAULT_LOW_LIMIT = 36
PR_DEFAULT_HIGH_LIMIT = 75
PR_DEFAULT_LOW_LIMIT = -75
SPEED_DEFAULT_HIGH_LIMIT = 174.2
SPEED_DEFAULT_LOW_LIMIT = -174.2

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("NIMATRO"),
        "ioc_launcher_class": ProcServLauncher,
        "macros": {
            "AREA_HIGH_LIMIT": AREA_DEFAULT_HIGH_LIMIT,
            "AREA_LOW_LIMIT": AREA_DEFAULT_LOW_LIMIT,
            "PRESSURE_HIGH_LIMIT": PR_DEFAULT_HIGH_LIMIT,
            "PRESSURE_LOW_LIMIT": PR_DEFAULT_LOW_LIMIT,
            "SPEED_HIGH_LIMIT": SPEED_DEFAULT_HIGH_LIMIT,
            "SPEED_LOW_LIMIT": SPEED_DEFAULT_LOW_LIMIT,
        },
    },
]

TEST_MODES = [TestModes.RECSIM]


class NimatroTests(unittest.TestCase):
    """
    Tests for the NIMA Trough IOC.

    This device uses LvDCOM and a vendor supplied driver that we are unable to test using our implementation (an
    interface to a subset of commands).

    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("CONTROL:START", timeout=30)

    @parameterized.expand(
        [
            ("low limit", AREA_DEFAULT_LOW_LIMIT),
            ("test_value_1", 93),
            ("test_value_2", 230),
            ("high limit", AREA_DEFAULT_HIGH_LIMIT),
        ]
    )
    def test_GIVEN_running_ioc_WHEN_set_target_area_sp_THEN_target_area_updated(self, _, area):
        expected_value = area
        self.ca.set_pv_value("AREA:SP", expected_value)

        self.ca.assert_that_pv_is("AREA:SP:RBV", expected_value)

    @parameterized.expand(
        [
            ("low limit check", AREA_DEFAULT_LOW_LIMIT - 1),
            ("high limit check", AREA_DEFAULT_HIGH_LIMIT + 1),
        ]
    )
    def test_GIVEN_running_ioc_WHEN_set_invalid_target_area_sp_THEN_record_bounded(self, _, area):
        expected_value = area
        self.ca.set_pv_value("AREA:SP", expected_value)

        self.ca.assert_that_pv_is_within_range(
            "AREA:SP:RBV", AREA_DEFAULT_LOW_LIMIT, AREA_DEFAULT_HIGH_LIMIT
        )

    @parameterized.expand(
        [
            (
                "high_limit_check",
                AREA_DEFAULT_LOW_LIMIT,
                AREA_DEFAULT_HIGH_LIMIT,
                AREA_DEFAULT_HIGH_LIMIT + 1,
            ),
            (
                "low_limit_check",
                AREA_DEFAULT_LOW_LIMIT,
                AREA_DEFAULT_HIGH_LIMIT,
                AREA_DEFAULT_LOW_LIMIT - 1,
            ),
            (
                "within_range_test",
                AREA_DEFAULT_LOW_LIMIT,
                AREA_DEFAULT_HIGH_LIMIT,
                AREA_DEFAULT_HIGH_LIMIT - 1,
            ),
        ]
    )
    def test_GIVEN_area_limits_explicitly_provided_WHEN_area_sp_written_THEN_sp_is_coerced_into_limits(
        self, _, low_limit, high_limit, expected_value
    ):
        with self._ioc.start_with_macros(
            {"AREA_HIGH_LIMIT": high_limit, "AREA_LOW_LIMIT": low_limit}, pv_to_wait_for="DISABLE"
        ):
            self.ca.set_pv_value("AREA:SP", expected_value)

            if high_limit >= expected_value >= low_limit:
                self.ca.assert_that_pv_is("AREA:SP:RBV", expected_value)
            else:
                self.ca.assert_that_pv_is_within_range("AREA:SP:RBV", low_limit, high_limit)

    @parameterized.expand(
        [
            (
                "high_limit_check",
                PR_DEFAULT_LOW_LIMIT,
                PR_DEFAULT_HIGH_LIMIT,
                PR_DEFAULT_HIGH_LIMIT + 1,
            ),
            (
                "low_limit_check",
                PR_DEFAULT_LOW_LIMIT,
                PR_DEFAULT_HIGH_LIMIT,
                PR_DEFAULT_LOW_LIMIT - 1,
            ),
            (
                "with_range_test",
                PR_DEFAULT_LOW_LIMIT,
                PR_DEFAULT_HIGH_LIMIT,
                PR_DEFAULT_HIGH_LIMIT - 1,
            ),
        ]
    )
    def test_GIVEN_pressure_limits_explicitly_provided_WHEN_pressure_sp_written_THEN_sp_is_coerced_into_limits(
        self, _, low_limit, high_limit, expected_value
    ):
        with self._ioc.start_with_macros(
            {"PRESSURE_HIGH_LIMIT": high_limit, "PRESSURE_LOW_LIMIT": low_limit},
            pv_to_wait_for="DISABLE",
        ):
            self.ca.set_pv_value("PRESSURE:SP", expected_value)

            if high_limit >= expected_value >= low_limit:
                self.ca.assert_that_pv_is("PRESSURE:SP:RBV", expected_value)
            else:
                self.ca.assert_that_pv_is_within_range("PRESSURE:SP:RBV", low_limit, high_limit)

    @parameterized.expand(
        [
            (
                "high_limit_check",
                SPEED_DEFAULT_LOW_LIMIT,
                SPEED_DEFAULT_HIGH_LIMIT,
                SPEED_DEFAULT_HIGH_LIMIT + 1,
            ),
            (
                "low_limit_check",
                SPEED_DEFAULT_LOW_LIMIT,
                SPEED_DEFAULT_HIGH_LIMIT,
                SPEED_DEFAULT_LOW_LIMIT - 1,
            ),
            (
                "with_range_test",
                SPEED_DEFAULT_LOW_LIMIT,
                SPEED_DEFAULT_HIGH_LIMIT,
                SPEED_DEFAULT_HIGH_LIMIT - 1,
            ),
        ]
    )
    def test_GIVEN_speed_limits_explicitly_provided_WHEN_speed_sp_written_THEN_sp_is_coerced_into_limits(
        self, _, low_limit, high_limit, expected_value
    ):
        with self._ioc.start_with_macros(
            {"SPEED_HIGH_LIMIT": high_limit, "SPEED_LOW_LIMIT": low_limit}, pv_to_wait_for="DISABLE"
        ):
            self.ca.set_pv_value("SPEED:SP", expected_value)

            if high_limit >= expected_value >= low_limit:
                self.ca.assert_that_pv_is("SPEED:SP:RBV", expected_value)
            else:
                self.ca.assert_that_pv_is_within_range("SPEED:SP:RBV", low_limit, high_limit)

    @parameterized.expand(
        [
            ("low limit", PR_DEFAULT_LOW_LIMIT),
            ("test_value_1", 10.0),
            ("test_value_2", 34.2),
            ("high limit", PR_DEFAULT_HIGH_LIMIT),
        ]
    )
    def test_GIVEN_running_ioc_WHEN_set_target_pressure_sp_THEN_target_pressure_updated(
        self, _, pressure
    ):
        expected_value = pressure
        self.ca.set_pv_value("PRESSURE:SP", expected_value)

        self.ca.assert_that_pv_is("PRESSURE:SP:RBV", expected_value)

    @parameterized.expand([("low limit check", -76.0), ("high limit check", 76.0)])
    def test_GIVEN_running_ioc_WHEN_set_invalid_target_pressure_sp_THEN_record_bounded(
        self, _, pressure
    ):
        expected_value = pressure
        self.ca.set_pv_value("PRESSURE:SP", expected_value)

        self.ca.assert_that_pv_is_within_range("PRESSURE:SP", -75, 75)

    @parameterized.expand(
        [
            ("low limit", SPEED_DEFAULT_LOW_LIMIT),
            ("test_value_1", -23.5),
            ("test_value_2", 34.2),
            ("high limit", SPEED_DEFAULT_HIGH_LIMIT),
        ]
    )
    def test_GIVEN_running_ioc_WHEN_set_target_speed_sp_THEN_target_speed_updated(self, _, speed):
        expected_value = speed
        self.ca.set_pv_value("SPEED:SP", expected_value)

        self.ca.assert_that_pv_is("SPEED", expected_value)

    @parameterized.expand(
        [
            ("low limit check", SPEED_DEFAULT_LOW_LIMIT - 1),
            ("high limit check", SPEED_DEFAULT_HIGH_LIMIT + 1),
        ]
    )
    def test_GIVEN_running_ioc_WHEN_set_invalid_target_speed_sp_THEN_record_bounded(self, _, speed):
        expected_value = speed
        self.ca.set_pv_value("SPEED:SP", expected_value)

        self.ca.assert_that_pv_is_within_range("SPEED:SP:RBV", -174.2, 174.2)
