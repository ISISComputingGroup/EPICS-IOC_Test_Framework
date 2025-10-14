import contextlib
import os
import threading
import typing
import unittest
from typing import Any

from utils.channel_access import ChannelAccess
from utils.emulator_launcher import EmulatorLauncher
from utils.ioc_launcher import BaseLauncher, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

PREFIX = os.environ.get("testing_prefix") or os.environ.get("MYPVPREFIX")

SMALL = 0.002  # Limited by rounding in cryosms ioc


def local_cryosms_pv(pv: str, iocnum: int) -> str:
    return f"{PREFIX}CRYOSMS_{iocnum:02d}:{pv}"


T_TO_A = 0.00029


def cryosms_macros(iocnum: int) -> dict[str, Any]:
    return {
        "MAX_CURR": 34.92,
        "T_TO_A": T_TO_A,
        "MAX_VOLT": 5,
        "WRITE_UNIT": "AMPS",
        "DISPLAY_UNIT": "GAUSS",
        "RAMP_FILE": r"C:\\Instrument\\Apps\\EPICS\\support\\cryosms\\master\\ramps\\default.txt",
        "MID_TOLERANCE": 999999999,  # 0.1
        "TARGET_TOLERANCE": 999999999,  # 0.1
        "ALLOW_PERSIST": "No",
        "USE_SWITCH": "No",
        "FAST_FILTER_VALUE": 1,
        "FILTER_VALUE": 0.1,
        "NPP": 0.0005,
        "FAST_PERSISTENT_SETTLETIME": 0,
        "PERSISTENT_SETTLETIME": 0,  # 60 on HIFI
        "NON_PERSISTENT_SETTLETIME": 0,  # Should not be used in ZF mode
        "SWITCH_TEMP_PV": local_cryosms_pv("SIM:SWITCH:TEMP", iocnum),
        "SWITCH_HIGH": 3.7,
        "SWITCH_LOW": 3.65,
        "SWITCH_STABLE_NUMBER": 10,
        "SWITCH_TIMEOUT": 300,
        "HEATER_TOLERANCE": 0.2,
        "HEATER_OFF_TEMP": 3.65,
        "HEATER_ON_TEMP": 3.7,
        "HEATER_OUT": "NULL",
        "USE_MAGNET_TEMP": "No",
        "MAGNET_TEMP_PV": "NULL",
        "MAX_MAGNET_TEMP": 5.5,
        "MIN_MAGNET_TEMP": 0,
        "COMP_OFF_ACT": "No",
        "NO_OF_COMP": 0,
        "MIN_NO_OF_COMP": 0,
        "COMP_1_STAT_PV": "NULL",
        "COMP_2_STAT_PV": "NULL",
        "HOLD_TIME_ZERO": 0,  # Should not be used in ZF mode
        "HOLD_TIME": 0,  # Should not be used in ZF mode
        "VOLT_STABILITY_DURATION": 1,
        "VOLT_TOLERANCE": 0.2,
        "FAST_RATE": 0.5,
        "RESTORE_WRITE_UNIT_TIMEOUT": 10,
        "CRYOMAGNET": "No",
    }


def cryosms_ioc(iocnum: int) -> dict[str, Any]:
    return {
        "name": f"CRYOSMS_{iocnum:02d}",
        "directory": get_default_ioc_dir("CRYOSMS", iocnum=iocnum),
        "emulator": "cryogenic_sms",
        "emulator_id": f"cryogenic_sms_{iocnum}",
        "speed": 1_000_000_000,
        "macros": cryosms_macros(iocnum),
    }


def group3_hall_probe_ioc(iocnum: int) -> dict[str, Any]:
    return {
        "name": f"G3HALLPR_{iocnum:02d}",
        "directory": get_default_ioc_dir("G3HALLPR", iocnum=iocnum),
        "emulator": "group3hallprobe",
        "emulator_id": f"group3hallprobe_{iocnum}",
        "macros": {
            "FIELD_SCAN_RATE": ".1 second",
            "TEMP_SCAN_RATE": ".1 second",
            "NAME0": "X",
            "NAME1": "Y",
            "NAME2": "Z",
            "SCALE0": 1,
            "SCALE1": 1,
            "SCALE2": 1,
            "FLNK0": f"{PREFIX}ZFHIFI_01:MAGNETOMETER:X{iocnum}:READINGS_UPDATED.PROC CA",
            "FLNK1": f"{PREFIX}ZFHIFI_01:MAGNETOMETER:Y{iocnum}:READINGS_UPDATED.PROC CA",
            "FLNK2": f"{PREFIX}ZFHIFI_01:MAGNETOMETER:Z{iocnum}:READINGS_UPDATED.PROC CA",
        },
    }


def zf_ioc() -> dict[str, Any]:
    return {
        "name": "ZFHIFI_01",
        "directory": get_default_ioc_dir("ZFHIFI"),
        "macros": {
            "PSU_X": f"{PREFIX}CRYOSMS_01",
            "PSU_Y": f"{PREFIX}CRYOSMS_02",
            "PSU_Z": f"{PREFIX}CRYOSMS_03",
            "MAGNETOMETER_X1": f"{PREFIX}G3HALLPR_01:0",
            "MAGNETOMETER_Y1": f"{PREFIX}G3HALLPR_01:1",
            "MAGNETOMETER_Z1": f"{PREFIX}G3HALLPR_01:2",
            "MAGNETOMETER_X2": f"{PREFIX}G3HALLPR_02:0",
            "MAGNETOMETER_Y2": f"{PREFIX}G3HALLPR_02:1",
            "MAGNETOMETER_Z2": f"{PREFIX}G3HALLPR_02:2",
            "PSU_X_MIN": -15,
            "PSU_X_MAX": 15,
            "PSU_Y_MIN": -15,
            "PSU_Y_MAX": 15,
            "PSU_Z_MIN": -15,
            "PSU_Z_MAX": 15,
        },
    }


IOCS = [
    cryosms_ioc(1),
    cryosms_ioc(2),
    cryosms_ioc(3),
    group3_hall_probe_ioc(1),
    group3_hall_probe_ioc(2),
    zf_ioc(),
]


TEST_MODES = [TestModes.DEVSIM]


MAGNETOMETERS = ("X1", "Y1", "Z1", "X2", "Y2", "Z2")
AXES = ("X", "Y", "Z")


class ZeroFieldHifiTests(unittest.TestCase):
    """
    Tests for the HIFI zero field controller IOC.
    """

    def setUp(self):
        def ca_lewis_ioc(
            ioc: str, emulator: str, iocnum: int, timeout: float = 10.0
        ) -> tuple[ChannelAccess, EmulatorLauncher, BaseLauncher]:
            ca = ChannelAccess(
                default_timeout=timeout, device_prefix=f"{ioc}_{iocnum:02d}", default_wait_time=0.0
            )
            lewis, ioc_instance = get_running_lewis_and_ioc(
                f"{emulator}_{iocnum}", f"{ioc}_{iocnum:02d}"
            )
            assert isinstance(lewis, EmulatorLauncher)
            return ca, lewis, ioc_instance

        self.x_psu_ca, self.x_psu_lewis, self.x_psu_ioc = ca_lewis_ioc(
            "CRYOSMS", "cryogenic_sms", 1, timeout=120
        )
        self.y_psu_ca, self.y_psu_lewis, self.y_psu_ioc = ca_lewis_ioc(
            "CRYOSMS", "cryogenic_sms", 2, timeout=120
        )
        self.z_psu_ca, self.z_psu_lewis, self.z_psu_ioc = ca_lewis_ioc(
            "CRYOSMS", "cryogenic_sms", 3, timeout=120
        )

        self.probe1_ca, self.probe1_lewis, self.probe1_ioc = ca_lewis_ioc(
            "G3HALLPR", "group3hallprobe", 1
        )
        self.probe2_ca, self.probe2_lewis, self.probe2_ioc = ca_lewis_ioc(
            "G3HALLPR", "group3hallprobe", 2
        )

        self.ca = ChannelAccess(
            default_timeout=10, device_prefix="ZFHIFI_01", default_wait_time=0.0
        )

        self.backdoor_set_raw_meas_fields(x1=0, y1=0, z1=0, x2=0, y2=0, z2=0)

        self.ca.set_pv_value("FEEDBACK", 1)
        self.ca.set_pv_value("STATEMACHINE:LOOP_DELAY", 250)
        self.ca.set_pv_value("STATEMACHINE:WRITE_TIMEOUT", 10)
        self.ca.set_pv_value("AUTOFEEDBACK", 0, sleep_after_set=5)
        self.ca.assert_that_pv_is("STATUS", "No error", timeout=30)

        self.ca.set_pv_value("DEBUG", 1)

        for psu in [self.x_psu_ca, self.y_psu_ca, self.z_psu_ca]:
            psu.set_pv_value("HEATER:STAT:_SP", "ON")

        self.wait_for_psus_ready()

        for magnetometer in MAGNETOMETERS:
            for axis in AXES:
                self.ca.set_pv_value(f"MAGNETOMETER:{magnetometer}:INH_{axis}", 0)
            self.ca.set_pv_value(f"MAGNETOMETER:{magnetometer}:PERSIST_GRAD", 0)
            self.ca.set_pv_value(f"MAGNETOMETER:{magnetometer}:OFFSET", 0)

        for axis in AXES:
            self.ca.set_pv_value(f"OUTPUT:{axis}:SP", 0)

        for axis in AXES:
            self.ca.assert_that_pv_is_number(f"OUTPUT:{axis}", 0)

        self.wait_for_psus_ready(x=0, y=0, z=0)

    def wait_for_psus_ready(
        self, *, x: float | None = None, y: float | None = None, z: float | None = None
    ) -> None:
        for psu in [self.x_psu_ca, self.y_psu_ca, self.z_psu_ca]:
            psu.assert_that_pv_is("INIT", "Startup complete")

        if x is not None:
            self.x_psu_ca.assert_that_pv_is_number("OUTPUT", x, tolerance=SMALL)
        if y is not None:
            self.y_psu_ca.assert_that_pv_is_number("OUTPUT", y, tolerance=SMALL)
        if z is not None:
            self.z_psu_ca.assert_that_pv_is_number("OUTPUT", z, tolerance=SMALL)

        for psu in [self.x_psu_ca, self.y_psu_ca, self.z_psu_ca]:
            psu.assert_that_pv_is("STAT", "Ready")
            psu.assert_that_pv_is("RAMP:STAT", "HOLDING ON TARGET")

    def backdoor_set_raw_meas_fields(
        self,
        *,
        x1: float | None = None,
        x2: float | None = None,
        y1: float | None = None,
        y2: float | None = None,
        z1: float | None = None,
        z2: float | None = None,
    ):
        for idx, value in enumerate([x1, y1, z1]):
            if value is not None:
                self.probe1_lewis.backdoor_run_function_on_device(
                    "backdoor_set_field", [idx, value]
                )

        for idx, value in enumerate([x2, y2, z2]):
            if value is not None:
                self.probe2_lewis.backdoor_run_function_on_device(
                    "backdoor_set_field", [idx, value]
                )

    def test_WHEN_magnetometer_readings_set_THEN_reflected_in_zf_ioc(self):
        self.backdoor_set_raw_meas_fields(x1=1, y1=2, z1=3, x2=1, y2=2, z2=3)

        self.ca.assert_that_pv_is_number("FIELD:X", 1, tolerance=SMALL)
        self.ca.assert_that_pv_is_number("FIELD:Y", 2, tolerance=SMALL)
        self.ca.assert_that_pv_is_number("FIELD:Z", 3, tolerance=SMALL)

    def test_WHEN_magnetometer_readings_too_high_THEN_zf_says_magnetometer_invalid(self):
        self.backdoor_set_raw_meas_fields(x1=999999999999, y1=2, z1=3, x2=999999999999, y2=5, z2=6)
        self.ca.assert_that_pv_is("STATUS", "Magnetometer data invalid")
        self.backdoor_set_raw_meas_fields(x1=1, y1=2, z1=3, x2=1, y2=2, z2=3)
        self.ca.assert_that_pv_is("STATUS", "No error")

    def test_WHEN_magnetometer_disconnected_THEN_reflected_in_zf_ioc(self):
        for probe in [self.probe1_lewis, self.probe2_lewis]:
            with probe.backdoor_simulate_disconnected_device():
                self.ca.assert_that_pv_is("STATUS", "No new magnetometer data", timeout=30)
            self.ca.assert_that_pv_is("STATUS", "No error", timeout=30)

    def test_WHEN_psu_disconnected_THEN_reflected_in_zf_ioc(self):
        for psu in [self.x_psu_lewis, self.y_psu_lewis, self.z_psu_lewis]:
            self.ca.set_pv_value("AUTOFEEDBACK", 0)
            self.wait_for_psus_ready()
            with psu.backdoor_simulate_disconnected_device():
                self.ca.set_pv_value("AUTOFEEDBACK", 1)
                self.ca.assert_that_pv_is("STATUS", "Power supply invalid", timeout=120)
                self.ca.set_pv_value("AUTOFEEDBACK", 0)
            self.ca.assert_that_pv_is("STATUS", "No error", timeout=300)

    def test_WHEN_has_a_persistent_gradient_THEN_magnetometer_readings_adjusted_correctly(self):
        y1_raw = 100
        y2_raw = 200
        diff = y2_raw - y1_raw
        self.backdoor_set_raw_meas_fields(x1=0, y1=y1_raw, z1=0, x2=0, y2=y2_raw, z2=0)
        self.ca.assert_that_pv_is_number("PERSISTENT_GRADIENT", diff, tolerance=SMALL)

        y1_persist_grad = 2
        y2_persist_grad = 3
        self.ca.set_pv_value("MAGNETOMETER:Y1:PERSIST_GRAD", y1_persist_grad)
        self.ca.set_pv_value("MAGNETOMETER:Y2:PERSIST_GRAD", y2_persist_grad)

        expected_y1 = y1_raw - (diff * y1_persist_grad)
        expected_y2 = y2_raw - (diff * y2_persist_grad)

        self.ca.assert_that_pv_is_number("PERSISTENT_GRADIENT", diff, tolerance=SMALL)
        self.ca.assert_that_pv_is_number("MAGNETOMETER:Y1:RAW", y1_raw, tolerance=SMALL)
        self.ca.assert_that_pv_is_number("MAGNETOMETER:Y2:RAW", y2_raw, tolerance=SMALL)

        self.ca.assert_that_pv_is_number("MAGNETOMETER:Y1", expected_y1, tolerance=SMALL)
        self.ca.assert_that_pv_is_number("MAGNETOMETER:Y2", expected_y2, tolerance=SMALL)
        self.ca.assert_that_pv_is_number(
            "FIELD:Y", (expected_y1 + expected_y2) / 2.0, tolerance=SMALL
        )

    def test_WHEN_has_offset_THEN_magnetometer_readings_adjusted_correctly(self):
        self.backdoor_set_raw_meas_fields(x1=1, y1=2, z1=3, x2=0, y2=0, z2=0)
        self.ca.set_pv_value("MAGNETOMETER:X1:OFFSET", 10)
        self.ca.set_pv_value("MAGNETOMETER:Y1:OFFSET", 100)
        self.ca.set_pv_value("MAGNETOMETER:Z1:OFFSET", 1000)

        self.ca.assert_that_pv_is_number("MAGNETOMETER:X1", 11, tolerance=SMALL)
        self.ca.assert_that_pv_is_number("MAGNETOMETER:Y1", 102, tolerance=SMALL)
        self.ca.assert_that_pv_is_number("MAGNETOMETER:Z1", 1003, tolerance=SMALL)

    def test_WHEN_has_inhomogenity_THEN_magnetometer_readings_adjusted_correctly(self):
        self.backdoor_set_raw_meas_fields(x1=1, y1=2, z1=3, x2=4, y2=5, z2=6)

        self.ca.set_pv_value("MAGNETOMETER:X1:INH_X", 10)
        self.ca.set_pv_value("MAGNETOMETER:X1:INH_Y", 100)
        self.ca.set_pv_value("MAGNETOMETER:X1:INH_Z", 1000)

        self.ca.set_pv_value("MAGNETOMETER:X2:INH_X", 20)
        self.ca.set_pv_value("MAGNETOMETER:X2:INH_Y", 200)
        self.ca.set_pv_value("MAGNETOMETER:X2:INH_Z", 2000)

        self.ca.set_pv_value("OUTPUT:X:SP", 7)
        self.ca.set_pv_value("OUTPUT:Y:SP", 8)
        self.ca.set_pv_value("OUTPUT:Z:SP", 9)

        self.wait_for_psus_ready(x=7, y=8, z=9)

        x_actual = typing.cast(float, self.ca.get_pv_value("OUTPUT:X"))
        y_actual = typing.cast(float, self.ca.get_pv_value("OUTPUT:Y"))
        z_actual = typing.cast(float, self.ca.get_pv_value("OUTPUT:Z"))
        self.assertAlmostEqual(x_actual, 7, delta=SMALL)
        self.assertAlmostEqual(y_actual, 8, delta=SMALL)
        self.assertAlmostEqual(z_actual, 9, delta=SMALL)

        self.ca.assert_that_pv_is_number(
            "MAGNETOMETER:X1", 1 - 10 * x_actual - 100 * y_actual - 1000 * z_actual, tolerance=SMALL
        )
        self.ca.assert_that_pv_is_number(
            "MAGNETOMETER:X2", 4 - 20 * x_actual - 200 * y_actual - 2000 * z_actual, tolerance=SMALL
        )

    def test_WHEN_autofeedback_on_and_field_always_too_low_THEN_output_goes_up_until_limit(self):
        self.ca.set_pv_value("AUTOFEEDBACK", 1)

        self.backdoor_set_raw_meas_fields(x1=-5, y1=-5, z1=-5, x2=-5, y2=-5, z2=-5)

        self.ca.assert_that_pv_is_number("OUTPUT:X:SP", 15, timeout=300)  # Limited by MAX
        self.ca.assert_that_pv_is_number("OUTPUT:Y:SP", 15, timeout=300)
        self.ca.assert_that_pv_is_number("OUTPUT:Z:SP", 15, timeout=300)

        self.ca.assert_that_pv_is("STATUS", "Power supply on limits")

    def test_WHEN_autofeedback_on_and_field_always_too_high_THEN_output_goes_down_until_limit(self):
        self.ca.set_pv_value("AUTOFEEDBACK", 1)

        self.backdoor_set_raw_meas_fields(x1=5, y1=5, z1=5, x2=5, y2=5, z2=5)

        self.ca.assert_that_pv_is_number("OUTPUT:X:SP", -15, timeout=300)  # Limited by MIN
        self.ca.assert_that_pv_is_number("OUTPUT:Y:SP", -15, timeout=300)
        self.ca.assert_that_pv_is_number("OUTPUT:Z:SP", -15, timeout=300)

        self.ca.assert_that_pv_is("STATUS", "Power supply on limits")

    @contextlib.contextmanager
    def _background_update_meas_fields(self, offset_x=0.0, offset_y=0.0, offset_z=0.0):
        ev = threading.Event()

        def _update_fields():
            while not ev.is_set():
                x_actual = typing.cast(float, self.ca.get_pv_value("OUTPUT:X"))
                y_actual = typing.cast(float, self.ca.get_pv_value("OUTPUT:Y"))
                z_actual = typing.cast(float, self.ca.get_pv_value("OUTPUT:Z"))

                x = round(x_actual + offset_x, 4)
                y = round(y_actual + offset_y, 4)
                z = round(z_actual + offset_z, 4)

                self.backdoor_set_raw_meas_fields(x1=x, x2=x, y1=y, y2=y, z1=z, z2=z)

        thread = threading.Thread(target=_update_fields)
        try:
            thread.start()
            yield
        finally:
            ev.set()
            thread.join()

    def test_WHEN_updating_fields_in_background_THEN_stabilizes_near_zero(self):
        with self._background_update_meas_fields(offset_x=1.23, offset_y=4.56, offset_z=7.89):
            self.ca.set_pv_value("AUTOFEEDBACK", 1)

            self.ca.assert_that_pv_is_number("OUTPUT:X", -1.23, timeout=300, tolerance=SMALL)
            self.ca.assert_that_pv_is_number("OUTPUT:Y", -4.56, timeout=300, tolerance=SMALL)
            self.ca.assert_that_pv_is_number("OUTPUT:Z", -7.89, timeout=300, tolerance=SMALL)

            self.ca.assert_that_pv_is_number("FIELD:X", 0, timeout=300, tolerance=SMALL)
            self.ca.assert_that_pv_is_number("FIELD:Y", 0, timeout=300, tolerance=SMALL)
            self.ca.assert_that_pv_is_number("FIELD:Z", 0, timeout=300, tolerance=SMALL)

    def test_WHEN_updating_fields_in_background_with_nonzero_sp_THEN_stabilizes_near_sp(self):
        with self._background_update_meas_fields(offset_x=1.23, offset_y=4.56, offset_z=7.89):
            self.ca.set_pv_value("FIELD:X:SP", -5)
            self.ca.set_pv_value("FIELD:Y:SP", 5)
            self.ca.set_pv_value("FIELD:Z:SP", 10)

            self.ca.set_pv_value("AUTOFEEDBACK", 1)

            self.ca.assert_that_pv_is_number("OUTPUT:X", -1.23 - 5, timeout=300, tolerance=SMALL)
            self.ca.assert_that_pv_is_number("OUTPUT:Y", -4.56 + 5, timeout=300, tolerance=SMALL)
            self.ca.assert_that_pv_is_number("OUTPUT:Z", -7.89 + 10, timeout=300, tolerance=SMALL)

            self.ca.assert_that_pv_is_number("FIELD:X", -5, timeout=300, tolerance=SMALL)
            self.ca.assert_that_pv_is_number("FIELD:Y", 5, timeout=300, tolerance=SMALL)
            self.ca.assert_that_pv_is_number("FIELD:Z", 10, timeout=300, tolerance=SMALL)
