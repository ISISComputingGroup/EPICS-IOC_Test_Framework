import contextlib
import itertools
import multiprocessing
import operator
import unittest
from time import sleep

import six

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list

ZF_DEVICE_PREFIX = "ZFCNTRL_01"
X_KEPCO_DEVICE_PREFIX = "KEPCO_01"
Y_KEPCO_DEVICE_PREFIX = "KEPCO_02"
Z_KEPCO_DEVICE_PREFIX = "KEPCO_03"
MAGNETOMETER_DEVICE_PREFIX = "ZFMAGFLD_01"


DEFAULT_LOW_OUTPUT_LIMIT = -100
DEFAULT_HIGH_OUTPUT_LIMIT = 100

X_KEPCO_VOLTAGE_LIMIT = 20
Y_KEPCO_VOLTAGE_LIMIT = 30
Z_KEPCO_VOLTAGE_LIMIT = 40


IOCS = [
    {
        "name": ZF_DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ZFCNTRL"),
        "started_text": "seq zero_field",
        "ioc_launcher_class": ProcServLauncher,
        "macros": {
            "OUTPUT_X_MIN": DEFAULT_LOW_OUTPUT_LIMIT,
            "OUTPUT_X_MAX": DEFAULT_HIGH_OUTPUT_LIMIT,
            "OUTPUT_Y_MIN": DEFAULT_LOW_OUTPUT_LIMIT,
            "OUTPUT_Y_MAX": DEFAULT_HIGH_OUTPUT_LIMIT,
            "OUTPUT_Z_MIN": DEFAULT_LOW_OUTPUT_LIMIT,
            "OUTPUT_Z_MAX": DEFAULT_HIGH_OUTPUT_LIMIT,

            "PSU_X": r"$(MYPVPREFIX){}".format(X_KEPCO_DEVICE_PREFIX),
            "PSU_Y": r"$(MYPVPREFIX){}".format(Y_KEPCO_DEVICE_PREFIX),
            "PSU_Z": r"$(MYPVPREFIX){}".format(Z_KEPCO_DEVICE_PREFIX),

            "MAGNETOMETER": r"$(MYPVPREFIX){}".format(MAGNETOMETER_DEVICE_PREFIX),

            "FEEDBACK": "1",
            "AMPS_PER_MG_X": "1",
            "AMPS_PER_MG_Y": "1",
            "AMPS_PER_MG_Z": "1",

            "OUTPUT_VOLTAGE_X_MAX": X_KEPCO_VOLTAGE_LIMIT,
            "OUTPUT_VOLTAGE_Y_MAX": Y_KEPCO_VOLTAGE_LIMIT,
            "OUTPUT_VOLTAGE_Z_MAX": Z_KEPCO_VOLTAGE_LIMIT,
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
            "RANGE": 1,
        }
    },
]


TEST_MODES = [TestModes.RECSIM]

FIELD_AXES = ["X", "Y", "Z"]
ZERO_FIELD = {"X": 0, "Y": 0, "Z": 0}

STABILITY_TOLERANCE = 1.0
LOOP_DELAY_MS = 100

AUTOFEEDBACK_VALUES = {True: "Auto-feedback", False: "Manual"}


def _update_fields_continuously(psu_amps_at_measured_zero):
    """
    This method is run in a background process for some tests which require the measured fields to "respond" to the
    power supply setpoints in a semi-realistic way.

    It makes new channel access objects so that we don't share locks with the existing ones, as that can cause issues
    with the update rate of this loop. In general this loop needs to be about as fast (or ideally faster) than the
    loop speed of the IOC, so that whenever the state machine picks up new magnetometer readings they reflect the
    latest power supply setpoints.
    """
    psu_ca = {
        "X": ChannelAccess(device_prefix=X_KEPCO_DEVICE_PREFIX),
        "Y": ChannelAccess(device_prefix=Y_KEPCO_DEVICE_PREFIX),
        "Z": ChannelAccess(device_prefix=Z_KEPCO_DEVICE_PREFIX),
    }

    controller_ca = ChannelAccess(device_prefix=ZF_DEVICE_PREFIX)
    magnetometer_ca = ChannelAccess(device_prefix=MAGNETOMETER_DEVICE_PREFIX)

    amps_per_mg = {
        "X": controller_ca.get_pv_value("P:X"),
        "Y": controller_ca.get_pv_value("P:Y"),
        "Z": controller_ca.get_pv_value("P:Z"),
    }

    while True:
        outputs = {axis: psu_ca[axis].get_pv_value("CURRENT:SP:RBV") for axis in FIELD_AXES}

        measured = {axis: (outputs[axis] - psu_amps_at_measured_zero[axis]) * (1.0 / amps_per_mg[axis]) for axis in
                    FIELD_AXES}

        for axis in FIELD_AXES:
            magnetometer_ca.set_pv_value("SIM:DAQ:{}".format(axis), measured[axis], sleep_after_set=0)


class Statuses(object):
    NO_ERROR = ("No error", ChannelAccess.Alarms.NONE)
    MAGNETOMETER_READ_ERROR = ("No new magnetometer data", ChannelAccess.Alarms.INVALID)
    MAGNETOMETER_OVERLOAD = ("Magnetometer overloaded", ChannelAccess.Alarms.MAJOR)
    MAGNETOMETER_DATA_INVALID = ("Magnetometer data invalid", ChannelAccess.Alarms.INVALID)
    PSU_INVALID = ("Power supply invalid", ChannelAccess.Alarms.INVALID)
    PSU_ON_LIMITS = ("Power supply on limits", ChannelAccess.Alarms.MAJOR)
    PSU_WRITE_FAILED = ("Power supply write failed", ChannelAccess.Alarms.INVALID)
    INVALID_PSU_LIMITS = ("PSU high limit<low limit", ChannelAccess.Alarms.MAJOR)


class AtSetpointStatuses(object):
    TRUE = "Yes"
    FALSE = "No"
    NA = "N/A"


class ZeroFieldTests(unittest.TestCase):
    """
    Tests for the muon zero field controller IOC.
    """
    def _set_simulated_measured_fields(self, fields, overload=False, wait_for_update=True):
        """
        Args:
            fields (dict[AnyStr, float]): A dictionary with the same keys as FIELD_AXES and values corresponding to the
              required fields
            overload (bool): whether to simulate the magnetometer being overloaded
            wait_for_update (bool): whether to wait for the statemachine to pick up the new readings
        """
        for axis in FIELD_AXES:
            self.magnetometer_ca.set_pv_value("SIM:DAQ:{}".format(axis), fields[axis], sleep_after_set=0)

        # Just overwrite the calculation to return a constant as we are not interested in testing the
        # overload logic in the magnetometer in these tests (that logic is tested separately).
        self.magnetometer_ca.set_pv_value("OVERLOAD:_CALC.CALC", "1" if overload else "0", sleep_after_set=0)

        if wait_for_update:
            for axis in FIELD_AXES:
                self.zfcntrl_ca.assert_that_pv_is("FIELD:{}".format(axis), fields[axis])
                self.zfcntrl_ca.assert_that_pv_is("FIELD:{}:MEAS".format(axis), fields[axis])

    def _set_user_setpoints(self, fields):
        """
        Args:
            fields (dict[AnyStr, float]): A dictionary with the same keys as FIELD_AXES and values corresponding to the
              required fields 
        """
        for axis in FIELD_AXES:
            self.zfcntrl_ca.set_pv_value("FIELD:{}:SP".format(axis), fields[axis], sleep_after_set=0)

    def _set_simulated_power_supply_currents(self, currents, wait_for_update=True):
        """
        Args:
            currents (dict[AnyStr, float]): A dictionary with the same keys as FIELD_AXES and values corresponding to
              the required currents
            wait_for_update (bool): whether to wait for the readback and setpoint readbacks to update
        """
        for axis in FIELD_AXES:
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:CURR:SP".format(axis), currents[axis], sleep_after_set=0)

        if wait_for_update:
            for axis in FIELD_AXES:
                self.zfcntrl_ca.assert_that_pv_is("OUTPUT:{}:CURR".format(axis), currents[axis])
                self.zfcntrl_ca.assert_that_pv_is("OUTPUT:{}:CURR:SP:RBV".format(axis), currents[axis])

    def _set_simulated_power_supply_voltages(self, voltages, wait_for_update=True):
        """
        Args:
            voltages (dict[AnyStr, float]): A dictionary with the same keys as FIELD_AXES and values corresponding to
              the required voltages
            wait_for_update (bool): whether to wait for the readback and setpoint readbacks to update
        """
        for axis in FIELD_AXES:
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:VOLT:SP".format(axis), voltages[axis], sleep_after_set=0)

        if wait_for_update:
            for axis in FIELD_AXES:
                self.zfcntrl_ca.assert_that_pv_is("OUTPUT:{}:VOLT".format(axis), voltages[axis])
                self.zfcntrl_ca.assert_that_pv_is("OUTPUT:{}:VOLT:SP:RBV".format(axis), voltages[axis])

    def _assert_at_setpoint(self, status):
        """
        Args:
            status (string): value of AT_SETPOINT PV (either Yes, No or N/A)
        """
        self.zfcntrl_ca.assert_that_pv_is("AT_SETPOINT", status)

    def _assert_status(self, status):
        """
        Args:
            status (Tuple[str, str]): the controller status and error to assert.
        """
        name, expected_alarm = status

        # Special case - this alarm should be suppressed in manual mode. This is because, in manual mode, the
        # scientists will intentionally apply large fields (which overload the magnetometer), but they do not want
        # alarms for this case as it is a "normal" mode of operation.
        if name == Statuses.MAGNETOMETER_OVERLOAD[0] and self.zfcntrl_ca.get_pv_value("AUTOFEEDBACK") == "Manual":
            expected_alarm = self.zfcntrl_ca.Alarms.NONE

        self.zfcntrl_ca.assert_that_pv_is("STATUS", name)
        self.zfcntrl_ca.assert_that_pv_alarm_is("STATUS", expected_alarm)

    def _set_autofeedback(self, autofeedback):
        self.zfcntrl_ca.set_pv_value("AUTOFEEDBACK", AUTOFEEDBACK_VALUES[autofeedback])

    def _set_scaling_factors(self, px, py, pz, fiddle):
        """
        Args:
            px (float): Amps per mG for the X axis.
            py (float): Amps per mG for the Y axis.
            pz (float): Amps per mG for the Z axis.
            fiddle (float): The feedback (sometimes called "fiddle") factor.
        """
        self.zfcntrl_ca.set_pv_value("P:X", px, sleep_after_set=0)
        self.zfcntrl_ca.set_pv_value("P:Y", py, sleep_after_set=0)
        self.zfcntrl_ca.set_pv_value("P:Z", pz, sleep_after_set=0)
        self.zfcntrl_ca.set_pv_value("P:FEEDBACK", fiddle, sleep_after_set=0)

    def _set_output_limits(self, lower_limits, upper_limits):
        """
        Args:
            lower_limits (dict[AnyStr, float]): A dictionary with the same keys as FIELD_AXES and values corresponding to
              the required output lower limits
            upper_limits (dict[AnyStr, float]): A dictionary with the same keys as FIELD_AXES and values corresponding to
              the required output upper limits
        """
        for axis in FIELD_AXES:
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:CURR:SP.DRVL".format(axis), lower_limits[axis], sleep_after_set=0)
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:CURR:SP.LOLO".format(axis), lower_limits[axis], sleep_after_set=0)
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:CURR:SP.DRVH".format(axis), upper_limits[axis], sleep_after_set=0)
            self.zfcntrl_ca.set_pv_value("OUTPUT:{}:CURR:SP.HIHI".format(axis), upper_limits[axis], sleep_after_set=0)

            self.zfcntrl_ca.set_pv_value(
                "OUTPUT:{}:CURR.LOLO".format(axis), lower_limits[axis], sleep_after_set=0)
            self.zfcntrl_ca.set_pv_value(
                "OUTPUT:{}:CURR.HIHI".format(axis), upper_limits[axis], sleep_after_set=0)

            self.zfcntrl_ca.set_pv_value(
                "OUTPUT:{}:CURR:SP:RBV.LOLO".format(axis), lower_limits[axis], sleep_after_set=0)
            self.zfcntrl_ca.set_pv_value(
                "OUTPUT:{}:CURR:SP:RBV.HIHI".format(axis), upper_limits[axis], sleep_after_set=0)

    @contextlib.contextmanager
    def _simulate_disconnected_magnetometer(self):
        """
        While this context manager is active, the magnetometer IOC will fail to take any new readings or process any PVs
        """
        self.magnetometer_ca.set_pv_value("DISABLE", 1, sleep_after_set=0)
        try:
            yield
        finally:
            self.magnetometer_ca.set_pv_value("DISABLE", 0, sleep_after_set=0)

    @contextlib.contextmanager
    def _simulate_invalid_magnetometer_readings(self):
        """
        While this context manager is active, any new readings from the magnetometer will be marked as INVALID
        """
        for axis in FIELD_AXES:
            self.magnetometer_ca.set_pv_value("DAQ:{}:_RAW.SIMS".format(axis),
                                              self.magnetometer_ca.Alarms.INVALID,
                                              sleep_after_set=0)

        # Wait for RAW PVs to process
        for axis in FIELD_AXES:
            self.magnetometer_ca.assert_that_pv_alarm_is("DAQ:{}:_RAW.SEVR".format(axis), self.magnetometer_ca.Alarms.INVALID)
        try:
            yield
        finally:
            for axis in FIELD_AXES:
                self.magnetometer_ca.set_pv_value("DAQ:{}:_RAW.SIMS".format(axis),
                                                  self.magnetometer_ca.Alarms.NONE, sleep_after_set=0)
            # Wait for RAW PVs to process
            for axis in FIELD_AXES:
                self.magnetometer_ca.assert_that_pv_alarm_is("DAQ:{}:_RAW.SEVR".format(axis),
                                                             self.magnetometer_ca.Alarms.NONE)

    @contextlib.contextmanager
    def _simulate_invalid_power_supply(self):
        """
        While this context manager is active, the readback values from all power supplies will be marked as INVALID
        (this simulates the device not being plugged in, for example)
        """
        pvs_to_make_invalid = ("CURRENT", "_CURRENT:SP:RBV", "OUTPUTMODE", "OUTPUTSTATUS", "VOLTAGE", "VOLTAGE:SP:RBV")

        for ca, pv in itertools.product((self.x_psu_ca, self.y_psu_ca, self.z_psu_ca), pvs_to_make_invalid):
            # 3 is the Enum value for an invalid alarm
            ca.set_pv_value("{}.SIMS".format(pv), 3, sleep_after_set=0)

        # Use a separate loop to avoid needing to wait for a 1-second scan 6 times.
        for ca, pv in itertools.product((self.x_psu_ca, self.y_psu_ca, self.z_psu_ca), pvs_to_make_invalid):
            ca.assert_that_pv_alarm_is(pv, ca.Alarms.INVALID)

        try:
            yield
        finally:
            for ca, pv in itertools.product((self.x_psu_ca, self.y_psu_ca, self.z_psu_ca), pvs_to_make_invalid):
                ca.set_pv_value("{}.SIMS".format(pv), 0, sleep_after_set=0)

            # Use a separate loop to avoid needing to wait for a 1-second scan 6 times.
            for ca, pv in itertools.product((self.x_psu_ca, self.y_psu_ca, self.z_psu_ca), pvs_to_make_invalid):
                ca.assert_that_pv_alarm_is(pv, ca.Alarms.NONE)

    @contextlib.contextmanager
    def _simulate_failing_power_supply_writes(self):
        """
        While this context manager is active, any writes to the power supply PVs will be ignored. This simulates the
        device being in local mode, for example. Note that this does not mark readbacks as invalid (for that, use
        _simulate_invalid_power_supply instead).
        """
        pvs = ["CURRENT:SP.DISP", "VOLTAGE:SP.DISP", "OUTPUTMODE:SP.DISP", "OUTPUTSTATUS:SP.DISP"]

        for ca, pv in itertools.product((self.x_psu_ca, self.y_psu_ca, self.z_psu_ca), pvs):
            ca.set_pv_value(pv, 1, sleep_after_set=0)
        try:
            yield
        finally:
            for ca, pv in itertools.product((self.x_psu_ca, self.y_psu_ca, self.z_psu_ca), pvs):
                ca.set_pv_value(pv, 0, sleep_after_set=0)

    @contextlib.contextmanager
    def _simulate_measured_fields_changing_with_outputs(self, psu_amps_at_measured_zero):
        """
        Calculates and sets somewhat realistic simulated measured fields based on the current values of power supplies.

        Args:
            psu_amps_at_measured_zero: Dictionary containing the Amps of the power supplies when the measured field
              corresponds to zero. i.e. if the system is told to go to zero field, these are the power supply readings
              it will require to get there.
        """
        # Always start at zero current
        self._set_simulated_power_supply_currents({"X": 0, "Y": 0, "Z": 0})

        thread = multiprocessing.Process(target=_update_fields_continuously, args=(psu_amps_at_measured_zero,))
        thread.start()
        try:
            yield
        finally:
            thread.terminate()

    def _wait_for_all_iocs_up(self):
        """
        Waits for the "primary" pv(s) from each ioc to be available
        """
        for ca in (self.x_psu_ca, self.y_psu_ca, self.z_psu_ca):
            ca.assert_that_pv_exists("CURRENT")
            ca.assert_that_pv_exists("CURRENT:SP")
            ca.assert_that_pv_exists("CURRENT:SP:RBV")

        for axis in FIELD_AXES:
            self.zfcntrl_ca.assert_that_pv_exists("FIELD:{}".format(axis))
            self.magnetometer_ca.assert_that_pv_exists("CORRECTEDFIELD:{}".format(axis))

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
        self.zfcntrl_ca.set_pv_value("STATEMACHINE:LOOP_DELAY", LOOP_DELAY_MS, sleep_after_set=0)
        self._set_autofeedback(False)

        # Set the magnetometer calibration to the 3x3 identity matrix
        for x, y in itertools.product(range(1, 3+1), range(1, 3+1)):
            self.magnetometer_ca.set_pv_value("SENSORMATRIX:{}{}".format(x, y), 1 if x == y else 0, sleep_after_set=0)

        self._set_simulated_measured_fields(ZERO_FIELD, overload=False)
        self._set_user_setpoints(ZERO_FIELD)
        self._set_simulated_power_supply_currents(ZERO_FIELD, wait_for_update=True)
        self._set_scaling_factors(1, 1, 1, 1)
        self._set_output_limits(
            lower_limits={"X": DEFAULT_LOW_OUTPUT_LIMIT, "Y": DEFAULT_LOW_OUTPUT_LIMIT, "Z": DEFAULT_LOW_OUTPUT_LIMIT},
            upper_limits={"X": DEFAULT_HIGH_OUTPUT_LIMIT, "Y": DEFAULT_HIGH_OUTPUT_LIMIT, "Z": DEFAULT_HIGH_OUTPUT_LIMIT},
        )

        self._assert_at_setpoint(AtSetpointStatuses.NA)
        self._assert_status(Statuses.NO_ERROR)

    def test_WHEN_ioc_is_started_THEN_it_is_not_disabled(self):
        self.zfcntrl_ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(FIELD_AXES))
    def test_WHEN_manual_mode_and_any_readback_value_is_not_equal_to_setpoint_THEN_at_setpoint_field_is_na(self, _, axis_to_vary):
        fields = {"X": 10, "Y": 20, "Z": 30}
        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)

        # Set one of the parameters to a completely different value
        self.zfcntrl_ca.set_pv_value("FIELD:{}:SP".format(axis_to_vary), 100, sleep_after_set=0)

        self._assert_at_setpoint(AtSetpointStatuses.NA)
        self._assert_status(Statuses.NO_ERROR)

    def test_GIVEN_manual_mode_and_magnetometer_not_overloaded_WHEN_readback_values_are_equal_to_setpoints_THEN_at_setpoint_field_is_na(self):
        fields = {"X": 55, "Y": 66, "Z": 77}
        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)

        self._assert_at_setpoint(AtSetpointStatuses.NA)
        self._assert_status(Statuses.NO_ERROR)

    def test_GIVEN_manual_mode_and_within_tolerance_WHEN_magnetometer_is_overloaded_THEN_status_overloaded_and_setpoint_field_is_na(self):
        fields = {"X": 55, "Y": 66, "Z": 77}
        self._set_simulated_measured_fields(fields, overload=True)
        self._set_user_setpoints(fields)

        self._assert_at_setpoint(AtSetpointStatuses.NA)
        self._assert_status(Statuses.MAGNETOMETER_OVERLOAD)

    def test_GIVEN_manual_mode_and_just_outside_tolerance_WHEN_magnetometer_is_overloaded_THEN_status_overloaded_and_setpoint_field_is_na(self):
        fields = {"X": 55, "Y": 66, "Z": 77}
        self._set_simulated_measured_fields(fields, overload=True)
        self._set_user_setpoints({k: v + 1.01 * STABILITY_TOLERANCE for k, v in six.iteritems(fields)})

        self._assert_at_setpoint(AtSetpointStatuses.NA)
        self._assert_status(Statuses.MAGNETOMETER_OVERLOAD)

    def test_GIVEN_manual_mode_and_just_within_tolerance_WHEN_magnetometer_is_overloaded_THEN_status_overloaded_and_setpoint_field_is_na(self):
        fields = {"X": 55, "Y": 66, "Z": 77}
        self._set_simulated_measured_fields(fields, overload=True)
        self._set_user_setpoints({k: v + 0.99 * STABILITY_TOLERANCE for k, v in six.iteritems(fields)})

        self._assert_at_setpoint(AtSetpointStatuses.NA)
        self._assert_status(Statuses.MAGNETOMETER_OVERLOAD)

    def test_WHEN_magnetometer_ioc_does_not_respond_THEN_status_is_magnetometer_read_error(self):
        fields = {"X": 1, "Y": 2, "Z": 3}
        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)

        with self._simulate_disconnected_magnetometer():
            self._assert_status(Statuses.MAGNETOMETER_READ_ERROR)
            for axis in FIELD_AXES:
                self.zfcntrl_ca.assert_that_pv_alarm_is("FIELD:{}".format(axis), self.zfcntrl_ca.Alarms.INVALID)
                self.zfcntrl_ca.assert_that_pv_alarm_is("FIELD:{}:MEAS".format(axis), self.zfcntrl_ca.Alarms.INVALID)

        # Now simulate recovery and assert error gets cleared correctly
        self._assert_status(Statuses.NO_ERROR)
        for axis in FIELD_AXES:
            self.zfcntrl_ca.assert_that_pv_alarm_is("FIELD:{}".format(axis), self.zfcntrl_ca.Alarms.NONE)
            self.zfcntrl_ca.assert_that_pv_alarm_is("FIELD:{}:MEAS".format(axis), self.zfcntrl_ca.Alarms.NONE)

    def test_WHEN_magnetometer_ioc_readings_are_invalid_THEN_status_is_magnetometer_invalid(self):
        fields = {"X": 1, "Y": 2, "Z": 3}
        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)

        with self._simulate_invalid_magnetometer_readings():
            self._assert_status(Statuses.MAGNETOMETER_DATA_INVALID)
            for axis in FIELD_AXES:
                self.zfcntrl_ca.assert_that_pv_alarm_is("FIELD:{}".format(axis), self.zfcntrl_ca.Alarms.INVALID)
                self.zfcntrl_ca.assert_that_pv_alarm_is("FIELD:{}:MEAS".format(axis), self.zfcntrl_ca.Alarms.INVALID)

        # Now simulate recovery and assert error gets cleared correctly
        self._assert_status(Statuses.NO_ERROR)
        for axis in FIELD_AXES:
            self.zfcntrl_ca.assert_that_pv_alarm_is("FIELD:{}".format(axis), self.zfcntrl_ca.Alarms.NONE)
            self.zfcntrl_ca.assert_that_pv_alarm_is("FIELD:{}:MEAS".format(axis), self.zfcntrl_ca.Alarms.NONE)

    def test_WHEN_power_supplies_are_invalid_THEN_status_is_power_supplies_invalid(self):
        fields = {"X": 1, "Y": 2, "Z": 3}
        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)
        self._set_autofeedback(True)

        with self._simulate_invalid_power_supply():
            self._assert_at_setpoint(AtSetpointStatuses.TRUE)  # Invalid power supplies do not mark the field as "not at setpoint"
            self._assert_status(Statuses.PSU_INVALID)

        # Now simulate recovery and assert error gets cleared correctly
        self._assert_at_setpoint(AtSetpointStatuses.TRUE)
        self._assert_status(Statuses.NO_ERROR)

    def test_WHEN_power_supplies_writes_fail_THEN_status_is_power_supply_writes_failed(self):
        fields = {"X": 1, "Y": 2, "Z": 3}
        self._set_simulated_measured_fields(fields, overload=False)

        # For this test we need changing fields so that we can detect that the writes failed
        self._set_user_setpoints({k: v + 10 * STABILITY_TOLERANCE for k, v in six.iteritems(fields)})
        # ... and we also need large limits so that we see that the writes failed as opposed to a limits error
        self._set_output_limits(
            lower_limits={k: -999999 for k in FIELD_AXES},
            upper_limits={k: 999999 for k in FIELD_AXES}
        )
        self._set_autofeedback(True)

        with self._simulate_failing_power_supply_writes():
            self._assert_status(Statuses.PSU_WRITE_FAILED)

        # Now simulate recovery and assert error gets cleared correctly
        self._assert_status(Statuses.NO_ERROR)

    def test_GIVEN_measured_field_and_setpoints_are_identical_THEN_setpoints_remain_unchanged(self):
        fields = {"X": 5, "Y": 10, "Z": -5}
        outputs = {"X": -1, "Y": -2, "Z": -3}

        self._set_simulated_measured_fields(fields, overload=False)
        self._set_user_setpoints(fields)
        self._set_simulated_power_supply_currents(outputs, wait_for_update=True)

        self._set_autofeedback(True)

        for axis in FIELD_AXES:
            self.zfcntrl_ca.assert_that_pv_is_number("OUTPUT:{}:CURR".format(axis), outputs[axis], tolerance=0.0001)
            self.zfcntrl_ca.assert_that_pv_value_is_unchanged("OUTPUT:{}:CURR".format(axis), wait=5)

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
        self._set_simulated_power_supply_currents({"X": 0, "Y": 0, "Z": 0}, wait_for_update=True)
        self._set_output_limits(
            lower_limits={k: -999999 for k in FIELD_AXES},
            upper_limits={k: 999999 for k in FIELD_AXES}
        )

        self._assert_status(Statuses.NO_ERROR)

        self._set_autofeedback(True)
        self._assert_at_setpoint(AtSetpointStatuses.FALSE)

        for axis in FIELD_AXES:
            self.zfcntrl_ca.assert_that_pv_value_over_time_satisfies_comparator("OUTPUT:{}:CURR".format(axis),
                                                                                wait=5, comparator=output_comparator)

        # In this happy-path case, we shouldn't be hitting any long timeouts, so loop times should remain fairly quick
        self.zfcntrl_ca.assert_that_pv_is_within_range("STATEMACHINE:LOOP_TIME", min_value=0, max_value=2*LOOP_DELAY_MS)

    def test_GIVEN_output_limits_too_small_for_required_field_THEN_status_error_and_alarm(self):
        self._set_output_limits(
            lower_limits={"X": -0.1, "Y": -0.1, "Z": -0.1},
            upper_limits={"X":  0.1, "Y":  0.1, "Z":  0.1},
        )

        # The measured field is smaller than the setpoint, i.e. the output needs to go up to the limits
        self._set_simulated_measured_fields({"X": -1, "Y": -1, "Z": -1})
        self._set_user_setpoints(ZERO_FIELD)
        self._set_simulated_power_supply_currents(ZERO_FIELD)

        self._set_autofeedback(True)

        self._assert_status(Statuses.PSU_ON_LIMITS)
        for axis in FIELD_AXES:
            # Value should be on one of the limits
            self.zfcntrl_ca.assert_that_pv_is_one_of("OUTPUT:{}:CURR:SP".format(axis), [-0.1, 0.1])
            # ...and in alarm
            self.zfcntrl_ca.assert_that_pv_alarm_is("OUTPUT:{}:CURR:SP".format(axis), self.zfcntrl_ca.Alarms.MAJOR)

    def test_GIVEN_limits_wrong_way_around_THEN_appropriate_error_raised(self):
        # Set upper limits < lower limits
        self._set_output_limits(
            lower_limits={"X": 0.1, "Y": 0.1, "Z": 0.1},
            upper_limits={"X": -0.1, "Y": -0.1, "Z": -0.1},
        )
        self._set_autofeedback(True)
        self._assert_status(Statuses.INVALID_PSU_LIMITS)

    @parameterized.expand(parameterized_list([
        {"X": 45.678, "Y": 0.123, "Z": 12.345},
        {"X": 0, "Y": 0, "Z": 0},
        {"X": -45.678, "Y": -0.123, "Z": -12.345},
    ]))
    def test_GIVEN_measured_values_updating_realistically_WHEN_in_auto_mode_THEN_converges_to_correct_answer(
            self, _, psu_amps_at_zero_field):
        self._set_output_limits(
            lower_limits={k: -100 for k in FIELD_AXES},
            upper_limits={k: 100 for k in FIELD_AXES}
        )
        self._set_user_setpoints({"X": 0, "Y": 0, "Z": 0})
        self._set_simulated_power_supply_currents({"X": 0, "Y": 0, "Z": 0})

        # Set fiddle small to get a relatively slow response, which should theoretically be stable
        self._set_scaling_factors(0.001, 0.001, 0.001, fiddle=0.05)

        with self._simulate_measured_fields_changing_with_outputs(psu_amps_at_measured_zero=psu_amps_at_zero_field):
            self._set_autofeedback(True)
            for axis in FIELD_AXES:
                self.zfcntrl_ca.assert_that_pv_is_number(
                    "OUTPUT:{}:CURR:SP:RBV".format(axis), psu_amps_at_zero_field[axis],
                    tolerance=STABILITY_TOLERANCE * 0.001, timeout=60)
                self.zfcntrl_ca.assert_that_pv_is_number(
                    "FIELD:{}".format(axis), 0.0, tolerance=STABILITY_TOLERANCE)

            self._assert_at_setpoint(AtSetpointStatuses.TRUE)
            self.zfcntrl_ca.assert_that_pv_value_is_unchanged("AT_SETPOINT", wait=20)
            self._assert_status(Statuses.NO_ERROR)

    @parameterized.expand(parameterized_list(FIELD_AXES))
    def test_GIVEN_output_is_off_WHEN_autofeedback_switched_on_THEN_psu_is_switched_back_on(self, _, axis):
        self.zfcntrl_ca.assert_setting_setpoint_sets_readback("Off", "OUTPUT:{}:STATUS".format(axis))
        self._set_autofeedback(True)
        self.zfcntrl_ca.assert_that_pv_is("OUTPUT:{}:STATUS".format(axis), "On")

    @parameterized.expand(parameterized_list(FIELD_AXES))
    def test_GIVEN_output_mode_is_voltage_WHEN_autofeedback_switched_on_THEN_psu_is_switched_to_current_mode(self, _, axis):
        self.zfcntrl_ca.assert_setting_setpoint_sets_readback(
            "Voltage", "OUTPUT:{}:MODE".format(axis), expected_alarm=self.zfcntrl_ca.Alarms.MAJOR)
        self._set_autofeedback(True)
        self.zfcntrl_ca.assert_that_pv_is("OUTPUT:{}:MODE".format(axis), "Current")

    @parameterized.expand(parameterized_list(FIELD_AXES))
    def test_GIVEN_output_is_off_and_cannot_write_to_psu_WHEN_autofeedback_switched_on_THEN_get_psu_write_error(self, _, axis):
        self.zfcntrl_ca.assert_setting_setpoint_sets_readback("Off", "OUTPUT:{}:STATUS".format(axis))
        with self._simulate_failing_power_supply_writes():
            self._set_autofeedback(True)
            self._assert_status(Statuses.PSU_WRITE_FAILED)

        # Check it can recover when writes work again
        self._assert_status(Statuses.NO_ERROR)
        self.zfcntrl_ca.assert_that_pv_is("OUTPUT:{}:STATUS".format(axis), "On")

    @parameterized.expand(parameterized_list(FIELD_AXES))
    def test_GIVEN_output_mode_is_voltage_and_cannot_write_to_psu_WHEN_autofeedback_switched_on_THEN_get_psu_write_error(self, _, axis):
        self.zfcntrl_ca.assert_setting_setpoint_sets_readback(
            "Voltage", "OUTPUT:{}:MODE".format(axis), expected_alarm=self.zfcntrl_ca.Alarms.MAJOR)

        with self._simulate_failing_power_supply_writes():
            self._set_autofeedback(True)
            self._assert_status(Statuses.PSU_WRITE_FAILED)

        # Check it can recover when writes work again
        self._assert_status(Statuses.NO_ERROR)
        self.zfcntrl_ca.assert_that_pv_is("OUTPUT:{}:MODE".format(axis), "Current")

    @parameterized.expand(parameterized_list([
        (True, True),
        (False, True),
        (True, False),
        (False, False),
    ]))
    def test_GIVEN_magnetometer_overloaded_THEN_error_suppressed_if_in_manual_mode(self, _, autofeedback, overloaded):
        self._set_autofeedback(autofeedback)
        self._set_simulated_measured_fields(ZERO_FIELD, overload=overloaded, wait_for_update=True)
        self._assert_status(Statuses.MAGNETOMETER_OVERLOAD if overloaded else Statuses.NO_ERROR)
        self.zfcntrl_ca.assert_that_pv_alarm_is(
            "STATUS", self.zfcntrl_ca.Alarms.MAJOR if overloaded and autofeedback else self.zfcntrl_ca.Alarms.NONE)

    def test_GIVEN_power_supply_voltage_limit_is_set_incorrectly_WHEN_going_into_auto_mode_THEN_correct_limits_applied(self):
        self._set_simulated_power_supply_voltages({"X": 0, "Y": 0, "Z": 0})

        self._set_autofeedback(True)

        self.zfcntrl_ca.assert_that_pv_is("OUTPUT:X:VOLT:SP:RBV", X_KEPCO_VOLTAGE_LIMIT)
        self.zfcntrl_ca.assert_that_pv_is("OUTPUT:Y:VOLT:SP:RBV", Y_KEPCO_VOLTAGE_LIMIT)
        self.zfcntrl_ca.assert_that_pv_is("OUTPUT:Z:VOLT:SP:RBV", Z_KEPCO_VOLTAGE_LIMIT)

    @parameterized.expand(parameterized_list(list(AUTOFEEDBACK_VALUES.keys())))
    def test_GIVEN_ioc_is_restarted_WHEN_feedback_autosave_is_set_to_true_THEN_feedback_mode_persists(self, _, autofeedback):
        with self._ioc.start_with_macros({"SAVEFEEDBACKMODE": "YES"}, pv_to_wait_for="OUTPUT:X:VOLT:SP:RBV"):
            self._set_autofeedback(autofeedback)
            self._ioc.force_manual_save()
            sleep(2)
            self._ioc.start_ioc(True)
            self.zfcntrl_ca.assert_that_pv_is("AUTOFEEDBACK", AUTOFEEDBACK_VALUES[autofeedback])
