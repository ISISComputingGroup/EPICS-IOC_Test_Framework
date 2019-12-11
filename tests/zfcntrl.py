import contextlib
import itertools
import operator
import unittest

import six
from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list

ZF_DEVICE_PREFIX = "ZFCNTRL_01"
X_KEPCO_DEVICE_PREFIX = "KEPCO_01"
Y_KEPCO_DEVICE_PREFIX = "KEPCO_02"
Z_KEPCO_DEVICE_PREFIX = "KEPCO_03"
MAGNETOMETER_DEVICE_PREFIX = "ZFMAGFLD_01"


DEFAULT_LOW_OUTPUT_LIMIT = -100
DEFAULT_HIGH_OUTPUT_LIMIT = 100


IOCS = [
    {
        "name": ZF_DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ZFCNTRL"),
        "started_text": "seq zero_field",
        "macros": {
            "OUTPUT_X_MIN": DEFAULT_LOW_OUTPUT_LIMIT,
            "OUTPUT_X_MAX": DEFAULT_HIGH_OUTPUT_LIMIT,
            "OUTPUT_Y_MIN": DEFAULT_LOW_OUTPUT_LIMIT,
            "OUTPUT_Y_MAX": DEFAULT_HIGH_OUTPUT_LIMIT,
            "OUTPUT_Z_MIN": DEFAULT_LOW_OUTPUT_LIMIT,
            "OUTPUT_Z_MAX": DEFAULT_HIGH_OUTPUT_LIMIT,

            "PSU_X": r"$(MYPVPREFIX){}:CURRENT".format(X_KEPCO_DEVICE_PREFIX),
            "PSU_Y": r"$(MYPVPREFIX){}:CURRENT".format(Y_KEPCO_DEVICE_PREFIX),
            "PSU_Z": r"$(MYPVPREFIX){}:CURRENT".format(Z_KEPCO_DEVICE_PREFIX),

            "MAGNETOMETER_TRIGGER": r"$(MYPVPREFIX){}:TAKEDATA".format(MAGNETOMETER_DEVICE_PREFIX),
            "MAGNETOMETER_X": r"$(MYPVPREFIX){}:X:CORRECTEDFIELD".format(MAGNETOMETER_DEVICE_PREFIX),
            "MAGNETOMETER_Y": r"$(MYPVPREFIX){}:Y:CORRECTEDFIELD".format(MAGNETOMETER_DEVICE_PREFIX),
            "MAGNETOMETER_Z": r"$(MYPVPREFIX){}:Z:CORRECTEDFIELD".format(MAGNETOMETER_DEVICE_PREFIX),
            "MAGNETOMETER_OVERLOAD": r"$(MYPVPREFIX){}:OVERLOAD".format(MAGNETOMETER_DEVICE_PREFIX),
            "MAGNETOMETER_MAGNITUDE": r"$(MYPVPREFIX){}:FIELDSTRENGTH".format(MAGNETOMETER_DEVICE_PREFIX),
        }
    },
    {
        "name": X_KEPCO_DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KEPCO", iocnum=1),
    },
    {
        "name": Y_KEPCO_DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KEPCO", iocnum=2),
    },
    {
        "name": Z_KEPCO_DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KEPCO", iocnum=3),
    },
    {
        "name": MAGNETOMETER_DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ZFMAGFLD"),
        "macros": {
            "OFFSET_X": 0,
            "OFFSET_Y": 0,
            "OFFSET_Z": 0,
            "SQNCR": r"$(MYPVPREFIX){}:INPUTS_UPDATED.PROC CA".format(ZF_DEVICE_PREFIX),
        }
    },
]


TEST_MODES = [TestModes.RECSIM]

FIELD_AXES = ["X", "Y", "Z"]
ZERO_FIELD = {"X": 0, "Y": 0, "Z": 0}

STABILITY_TOLERANCE = 1.0


class Statuses(object):
    NO_ERROR = ("No error", ChannelAccess.Alarms.NONE)
    MAGNETOMETER_READ_ERROR = ("No new magnetometer data", ChannelAccess.Alarms.MAJOR)
    MAGNETOMETER_OVERLOAD = ("Magnetometer overloaded", ChannelAccess.Alarms.MAJOR)
    MAGNETOMETER_DATA_INVALID = ("Magnetometer data invalid", ChannelAccess.Alarms.MAJOR)
    PSU_INVALID = ("Power supply invalid", ChannelAccess.Alarms.MAJOR)
    PSU_ON_LIMITS = ("Power supply on limits", ChannelAccess.Alarms.MAJOR)


class ZeroFieldTests(unittest.TestCase):
    """
    Tests for the muon zero field controller IOC.
    """
    def _set_simulated_measured_fields(self, fields, overload=False, wait_for_update=True):
        """
        Args:
            fields (dict[str, float]): A dictionary with the same keys as FIELD_AXES and values corresponding to the
              required fields
            overload (bool): whether to simulate the magnetometer being overloaded
            wait_for_update (bool): whether to wait for the statemachine to pick up the new readings
        """
        for axis in FIELD_AXES:
            self.magnetometer_ca.set_pv_value("SIM:DAQ:{}".format(axis), fields[axis], sleep_after_set=0)

        # Just overwrite the calculation to return a constant as we are not interested in testing the
        # overload logic here.
        self.magnetometer_ca.set_pv_value("OVERLOAD.CALC", "1" if overload else "0", sleep_after_set=0)

        if wait_for_update:
            for axis in FIELD_AXES:
                self.zfcntrl_ca.assert_that_pv_is("MAGNETOMETER:{}".format(axis), fields[axis])

    def _set_user_setpoints(self, fields):
        """
        Args:
            fields (dict[str, float]): A dictionary with the same keys as FIELD_AXES and values corresponding to the
              required fields 
        """
        for axis in FIELD_AXES:
            self.zfcntrl_ca.set_pv_value("FIELD:{}:SP".format(axis), fields[axis], sleep_after_set=0)

    def _set_simulated_outputs(self, fields, wait_for_update=True):
        """
        Args:
            fields (dict[str, float]): A dictionary with the same keys as FIELD_AXES and values corresponding to the
              required fields
            wait_for_update (bool): whether to wait for the readback and setpoint readbacks to update
        """
        for axis in FIELD_AXES:
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:SP".format(axis), fields[axis], sleep_after_set=0)

        if wait_for_update:
            for axis in FIELD_AXES:
                self.zfcntrl_ca.assert_that_pv_is("OUTPUT:{}".format(axis), fields[axis])
                self.zfcntrl_ca.assert_that_pv_is("OUTPUT:{}:SP:RBV".format(axis), fields[axis])

    def _assert_stable(self, stable):
        self.zfcntrl_ca.assert_that_pv_is("STABLE", "Stable" if stable else "Unstable")
        self.zfcntrl_ca.assert_that_pv_alarm_is("STABLE", self.zfcntrl_ca.Alarms.NONE if stable else self.zfcntrl_ca.Alarms.MAJOR)

    def _assert_status(self, status):
        name, alarm = status
        self.zfcntrl_ca.assert_that_pv_is("STATUS", name)
        self.zfcntrl_ca.assert_that_pv_alarm_is("STATUS", alarm)

    def _set_autofeedback(self, autofeedback):
        self.zfcntrl_ca.set_pv_value("AUTOFEEDBACK", "Auto-feedback" if autofeedback else "Manual")

    def _set_scaling_factors(self, px, py, pz, fiddle):
        self.zfcntrl_ca.set_pv_value("P:X", px, sleep_after_set=0)
        self.zfcntrl_ca.set_pv_value("P:Y", py, sleep_after_set=0)
        self.zfcntrl_ca.set_pv_value("P:Z", pz, sleep_after_set=0)
        self.zfcntrl_ca.set_pv_value("P:FEEDBACK", fiddle, sleep_after_set=0)

    def _set_output_limits(self, lower_limits, upper_limits):
        """
        Args:
            lower_limits (dict[str, float]): A dictionary with the same keys as FIELD_AXES and values corresponding to
              the required output lower limits
            upper_limits (dict[str, float]): A dictionary with the same keys as FIELD_AXES and values corresponding to
              the required output upper limits
        """
        for axis in FIELD_AXES:
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:SP.DRVL".format(axis), lower_limits[axis], sleep_after_set=0)
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:SP.LOLO".format(axis), lower_limits[axis], sleep_after_set=0)
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:SP.DRVH".format(axis), upper_limits[axis], sleep_after_set=0)
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:SP.HIHI".format(axis), upper_limits[axis], sleep_after_set=0)

            self.zfcntrl_ca.set_pv_value("OUTPUT:{}.LOLO".format(axis), lower_limits[axis], sleep_after_set=0)
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}.HIHI".format(axis), upper_limits[axis], sleep_after_set=0)

            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:SP:RBV.LOLO".format(axis), lower_limits[axis], sleep_after_set=0)
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:SP:RBV.HIHI".format(axis), upper_limits[axis], sleep_after_set=0)

    @contextlib.contextmanager
    def _simulate_disconnected_magnetometer(self):
        self.magnetometer_ca.set_pv_value("DISABLE", 1, sleep_after_set=0)
        try:
            yield
        finally:
            self.magnetometer_ca.set_pv_value("DISABLE", 0, sleep_after_set=0)

    @contextlib.contextmanager
    def _simulate_invalid_magnetometer_readings(self):
        for axis in FIELD_AXES:
            # 3 is the Enum value for an invalid alarm
            self.magnetometer_ca.set_pv_value("DAQ:{}:_RAW.SIMS".format(axis), 3, sleep_after_set=0)
        try:
            yield
        finally:
            for axis in FIELD_AXES:
                # 0 is the Enum value for no alarm
                self.magnetometer_ca.set_pv_value("DAQ:{}:_RAW.SIMS".format(axis), 0, sleep_after_set=0)

    @contextlib.contextmanager
    def _simulate_invalid_power_supply(self):
        for ca, pv in itertools.product((self.x_psu_ca, self.y_psu_ca, self.z_psu_ca), ("CURRENT", "CURRENT:SP:RBV")):
            # 3 is the Enum value for an invalid alarm
            ca.set_pv_value("{}.SIMS".format(pv), 3, sleep_after_set=0)
            ca.assert_that_pv_alarm_is(pv, ca.Alarms.INVALID)
        try:
            yield
        finally:
            for ca, pv in itertools.product((self.x_psu_ca, self.y_psu_ca, self.z_psu_ca),
                                            ("CURRENT", "CURRENT:SP:RBV")):
                ca.set_pv_value("{}.SIMS".format(pv), 0, sleep_after_set=0)
                ca.assert_that_pv_alarm_is(pv, ca.Alarms.NONE)

    def _wait_for_all_iocs_up(self):
        for ca in (self.x_psu_ca, self.y_psu_ca, self.z_psu_ca):
            ca.assert_that_pv_exists("CURRENT")
            ca.assert_that_pv_exists("CURRENT:SP")
            ca.assert_that_pv_exists("CURRENT:SP:RBV")

        for axis in FIELD_AXES:
            self.zfcntrl_ca.assert_that_pv_exists("FIELD:{}".format(axis))
            self.magnetometer_ca.assert_that_pv_exists("{}:CORRECTEDFIELD".format(axis))

    def setUp(self):
        _, self._ioc = get_running_lewis_and_ioc(None, ZF_DEVICE_PREFIX)

        timeout = 20
        self.zfcntrl_ca = ChannelAccess(device_prefix=ZF_DEVICE_PREFIX, default_timeout=timeout)
        self.magnetometer_ca = ChannelAccess(device_prefix=MAGNETOMETER_DEVICE_PREFIX, default_timeout=timeout)
        self.x_psu_ca = ChannelAccess(default_timeout=timeout, device_prefix=X_KEPCO_DEVICE_PREFIX)
        self.y_psu_ca = ChannelAccess(default_timeout=timeout, device_prefix=Y_KEPCO_DEVICE_PREFIX)
        self.z_psu_ca = ChannelAccess(default_timeout=timeout, device_prefix=Z_KEPCO_DEVICE_PREFIX)

        self._wait_for_all_iocs_up()

        self.zfcntrl_ca.set_pv_value("TOLERANCE", STABILITY_TOLERANCE, sleep_after_set=0)
        self._set_autofeedback(False)

        # Set the magnetometer calibration to the 3x3 identity matrix
        for x, y in itertools.product(range(1, 3+1), range(1, 3+1)):
            self.magnetometer_ca.set_pv_value("SENSORMATRIX:{}{}".format(x, y), 1 if x == y else 0, sleep_after_set=0)

        mock_fields = {"X": 0, "Y": 0, "Z": 0}
        self._set_simulated_measured_fields(mock_fields, overload=False)
        self._set_user_setpoints(mock_fields)
        self._set_simulated_outputs(mock_fields, wait_for_update=True)
        self._set_scaling_factors(1, 1, 1, 1)
        self._set_output_limits(
            lower_limits={"X": DEFAULT_LOW_OUTPUT_LIMIT, "Y": DEFAULT_LOW_OUTPUT_LIMIT, "Z": DEFAULT_LOW_OUTPUT_LIMIT},
            upper_limits={"X": DEFAULT_HIGH_OUTPUT_LIMIT, "Y": DEFAULT_HIGH_OUTPUT_LIMIT, "Z": DEFAULT_HIGH_OUTPUT_LIMIT},
        )

        self._assert_stable(True)
        self._assert_status(Statuses.NO_ERROR)

    def test_WHEN_ioc_is_started_THEN_it_is_not_disabled(self):
        self.zfcntrl_ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(FIELD_AXES))
    def test_WHEN_any_readback_value_is_not_equal_to_setpoint_THEN_field_is_marked_as_unstable(self, _, axis_to_vary):
        fields = {"X": 10, "Y": 20, "Z": 30}
        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)

        # Set one of the parameters to a completely different value
        self.zfcntrl_ca.set_pv_value("FIELD:{}:SP".format(axis_to_vary), 100, sleep_after_set=0)

        self._assert_stable(False)
        self._assert_status(Statuses.NO_ERROR)

    def test_GIVEN_magnetometer_not_overloaded_WHEN_readback_values_are_equal_to_setpoints_THEN_field_is_marked_as_stable(self):
        fields = {"X": 55, "Y": 66, "Z": 77}
        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)

        self._assert_stable(True)
        self._assert_status(Statuses.NO_ERROR)

    def test_GIVEN_within_tolerance_WHEN_magnetometer_is_overloaded_THEN_status_overloaded_and_stable(self):
        fields = {"X": 55, "Y": 66, "Z": 77}
        self._set_simulated_measured_fields(fields, overload=True)
        self._set_user_setpoints(fields)

        self._assert_stable(True)
        self._assert_status(Statuses.MAGNETOMETER_OVERLOAD)

    def test_GIVEN_just_outside_tolerance_WHEN_magnetometer_is_overloaded_THEN_status_overloaded_and_unstable(self):
        fields = {"X": 55, "Y": 66, "Z": 77}
        self._set_simulated_measured_fields(fields, overload=True)
        self._set_user_setpoints({k: v + 1.01 * STABILITY_TOLERANCE for k, v in six.iteritems(fields)})

        self._assert_stable(False)
        self._assert_status(Statuses.MAGNETOMETER_OVERLOAD)

    def test_GIVEN_just_within_tolerance_WHEN_magnetometer_is_overloaded_THEN_status_overloaded_and_stable(self):
        fields = {"X": 55, "Y": 66, "Z": 77}
        self._set_simulated_measured_fields(fields, overload=True)
        self._set_user_setpoints({k: v + 0.99 * STABILITY_TOLERANCE for k, v in six.iteritems(fields)})

        self._assert_stable(True)
        self._assert_status(Statuses.MAGNETOMETER_OVERLOAD)

    def test_WHEN_magnetometer_ioc_does_not_respond_THEN_status_is_magnetometer_read_error(self):
        fields = {"X": 1, "Y": 2, "Z": 3}
        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)

        with self._simulate_disconnected_magnetometer():
            self._assert_stable(False)
            self._assert_status(Statuses.MAGNETOMETER_READ_ERROR)

        # Now simulate recovery and assert error gets cleared correctly
        self._assert_stable(True)
        self._assert_status(Statuses.NO_ERROR)

    def test_WHEN_magnetometer_ioc_readings_are_invalid_THEN_status_is_magnetometer_invalid(self):
        fields = {"X": 1, "Y": 2, "Z": 3}
        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)

        with self._simulate_invalid_magnetometer_readings():
            self._assert_stable(False)
            self._assert_status(Statuses.MAGNETOMETER_DATA_INVALID)

        # Now simulate recovery and assert error gets cleared correctly
        self._assert_stable(True)
        self._assert_status(Statuses.NO_ERROR)

    def test_WHEN_power_supplies_are_invalid_THEN_status_is_power_supplies_invalid(self):
        fields = {"X": 1, "Y": 2, "Z": 3}
        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)
        self._set_autofeedback(True)

        with self._simulate_invalid_power_supply():
            self._assert_stable(False)
            self._assert_status(Statuses.PSU_INVALID)

        # Now simulate recovery and assert error gets cleared correctly
        self._assert_stable(True)
        self._assert_status(Statuses.NO_ERROR)

    def test_GIVEN_measured_field_and_setpoints_are_identical_THEN_setpoints_remain_unchanged(self):
        fields = {"X": 5, "Y": 10, "Z": -5}
        outputs = {"X": -1, "Y": -2, "Z": -3}

        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)
        self._set_simulated_outputs(outputs, wait_for_update=True)

        self._set_autofeedback(True)

        for axis in FIELD_AXES:
            self.zfcntrl_ca.assert_that_pv_is_number("OUTPUT:{}".format(axis), outputs[axis], tolerance=0.0001)
            self.zfcntrl_ca.assert_that_pv_value_is_unchanged("OUTPUT:{}".format(axis), wait=5)

    @parameterized.expand(parameterized_list([
        # If measured field is smaller than the setpoint, we want to adjust the output upwards to compensate
        (operator.sub, operator.gt, 1),
        # If measured field is larger than the setpoint, we want to adjust the output downwards to compensate
        (operator.add, operator.lt, 1),
        # If measured field is smaller than the setpoint, and A/mg is negative, we want to adjust the output downwards
        # to compensate
        (operator.sub, operator.lt, -1),
        # If measured field is larger than the setpoint, and A/mg is negative, we want to adjust the output upwards
        # to compensate
        (operator.add, operator.gt, -1),
        # If measured field is smaller than the setpoint, and A/mg is zero, then power supply output should remain
        # unchanged
        (operator.sub, operator.eq, 0),
        # If measured field is larger than the setpoint, and A/mg is zero, then power supply output should remain
        # unchanged
        (operator.add, operator.eq, 0),
    ]))
    def test_GIVEN_autofeedback_WHEN_measured_field_different_from_setpoints_THEN_power_supply_outputs_move_in_correct_direction(
            self, _, measured_field_modifier, output_comparator, scaling_factor):

        fields = {"X": 5, "Y": 0, "Z": -5}

        adjustment_amount = 10 * STABILITY_TOLERANCE  # To ensure that it is not considered stable to start with
        measured_fields = {k: measured_field_modifier(v, adjustment_amount) for k, v in six.iteritems(fields)}

        self._set_scaling_factors(scaling_factor, scaling_factor, scaling_factor, fiddle=1)
        self._set_simulated_measured_fields(measured_fields, overload=False)
        self._set_user_setpoints(fields)
        self._set_simulated_outputs({"X": 0, "Y": 0, "Z": 0}, wait_for_update=True)
        self._set_output_limits(
            lower_limits={k: -999999 for k in FIELD_AXES},
            upper_limits={k: 999999 for k in FIELD_AXES}
        )

        self._assert_status(Statuses.NO_ERROR)
        self._assert_stable(False)

        self._set_autofeedback(True)

        for axis in FIELD_AXES:
            self.zfcntrl_ca.assert_that_pv_value_over_time_satisfies_comparator("OUTPUT:{}".format(axis),
                                                                                wait=5, comparator=output_comparator)

    def test_GIVEN_output_limits_too_small_for_required_field_THEN_status_error_and_alarm(self):
        self._set_output_limits(
            lower_limits={"X": -0.1, "Y": -0.1, "Z": -0.1},
            upper_limits={"X":  0.1, "Y":  0.1, "Z":  0.1},
        )

        # The measured field is smaller than the setpoint, i.e. the output needs to go up to the limits
        self._set_simulated_measured_fields({"X": -1, "Y": -1, "Z": -1})
        self._set_user_setpoints(ZERO_FIELD)
        self._set_simulated_outputs(ZERO_FIELD)

        self._set_autofeedback(True)

        self._assert_status(Statuses.PSU_ON_LIMITS)
        for axis in FIELD_AXES:
            self.zfcntrl_ca.assert_that_pv_alarm_is("OUTPUT:{}:SP".format(axis), self.zfcntrl_ca.Alarms.MAJOR)
