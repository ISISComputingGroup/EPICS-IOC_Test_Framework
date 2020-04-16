import os
import unittest
import time

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir, EPICS_TOP, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import parameterized_list, ManagerMode, unstable_test

ioc_number = 1
DEVICE_PREFIX = "LSICORR_{:02d}".format(ioc_number)

LSICORR_PATH = os.path.join(EPICS_TOP, "support", "lsicorr", "master")
IOCS = [
    {
        "ioc_launcher_class": ProcServLauncher,
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LSICORR", iocnum=ioc_number),
        "started_text": "IOC started",
        "macros": {
        }
    }

]


TEST_MODES = [TestModes.DEVSIM]

PV_NAMES = ["CORRELATIONTYPE",
            "NORMALIZATION",
            "MEASUREMENTDURATION",
            "SWAPCHANNELS",
            "SAMPLINGTIMEMULTIT",
            "TRANSFERRATE",
            "OVERLOADLIMIT",
            "OVERLOADINTERVAL",
            "ERRORMSG",
            "EXPERIMENTNAME",
            "OUTPUTFILE",
            "START",
            "STOP",
            "CORRELATION_FUNCTION",
            "LAGS",
            "REPETITIONS",
            "CURRENT_REPETITION",
            "RUNNING",
            "CONNECTED",
            "SCATTERING_ANGLE",
            "SAMPLE_TEMP",
            "SOLVENT_VISCOSITY",
            "SOLVENT_REFRACTIVE_INDEX",
            "LASER_WAVELENGTH"]


SETTING_PVS = [("CORRELATIONTYPE", "CROSS"),
               ("NORMALIZATION", "SYMMETRIC"),
               ("MEASUREMENTDURATION", 30),
               ("SWAPCHANNELS", "ChB_ChA"),
               ("SAMPLINGTIMEMULTIT", "ns200"),
               ("TRANSFERRATE", "ms700"),
               ("OVERLOADLIMIT", 15),
               ("OVERLOADINTERVAL", 450),
               ("START", "YES"),
               ("STOP", "YES"),
               ("REPETITIONS", 5),
               ("SCATTERING_ANGLE", 4.4),
               ("SAMPLE_TEMP", 298),
               ("SOLVENT_VISCOSITY", 2200),
               ("SOLVENT_REFRACTIVE_INDEX", 2.2),
               ("LASER_WAVELENGTH", 580)]


class LSITests(unittest.TestCase):
    """
    Tests for LSi Correlator
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running("LSI")
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)

    def test_GIVEN_setting_pv_WHEN_pv_written_to_THEN_new_value_read_back(self):
        pv_name = "MEASUREMENTDURATION"
        pv_value = 1000

        self.ca.set_pv_value(pv_name, pv_value)
        self.ca.assert_that_pv_is_number(pv_name, pv_value)

    def test_GIVEN_setting_pv_WHEN_pv_written_to_with_invalid_value_THEN_value_not_updated(self):
        pv_name = "MEASUREMENTDURATION"
        original_value = self.ca.get_pv_value(pv_name)

        self.ca.set_pv_value(pv_name, -1)
        self.ca.assert_that_pv_is_number(pv_name, original_value)

    def test_GIVEN_integer_device_setting_WHEN_pv_written_to_with_a_float_THEN_value_is_rounded_before_setting(self):
        pv_name = "MEASUREMENTDURATION"
        new_value = 12.3

        self.ca.set_pv_value(pv_name, new_value)
        self.ca.assert_that_pv_is_number(pv_name, 12)

    def test_GIVEN_monitor_on_setting_pv_WHEN_pv_changed_THEN_monitor_gets_updated(self):
        pv_name = "MEASUREMENTDURATION"
        self.ca.set_pv_value(pv_name, 10.0)
        new_value = 12.3
        expected_value = 12.0

        with self.ca.assert_that_pv_monitor_is(pv_name, expected_value):
            self.ca.set_pv_value(pv_name + ":SP", new_value)

    def test_GIVEN_invalid_value_for_setting_WHEN_setting_pv_written_THEN_status_pv_updates_with_error(self):
        setting_pv = "MEASUREMENTDURATION"
        self.ca.set_pv_value(setting_pv, -1)
        error_message = "LSI --- wrong value assigned to MeasurementDuration"

        self.ca.assert_that_pv_is("ERRORMSG", error_message)

    @parameterized.expand([
        ("NORMALIZATION", ("SYMMETRIC", "COMPENSATED")),
        ("SWAPCHANNELS", ("ChA_ChB", "ChB_ChA")),
        ("CORRELATIONTYPE", ("AUTO", "CROSS")),
        ("TRANSFERRATE", ("ms100", "ms150", "ms200", "ms250", "ms300", "ms400", "ms500", "ms600", "ms700")),
        ("SAMPLINGTIMEMULTIT", ("ns12_5", "ns200", "ns400", "ns800", "ns1600", "ns3200"))
    ])
    def test_GIVEN_enum_setting_WHEN_setting_pv_written_to_THEN_new_value_read_back(self, pv, values):
        for value in values:
            self.ca.set_pv_value(pv, value, sleep_after_set=0.0)
            self.ca.assert_that_pv_is(pv, value)

    @parameterized.expand([
        ("OVERLOADLIMIT", "Mcps"),
        ("SCATTERING_ANGLE", "degree"),
        ("SAMPLE_TEMP", "K"),
        ("SOLVENT_VISCOSITY", "mPas"),
        ("SOLVENT_REFRACTIVE_INDEX", ""),
        ("LASER_WAVELENGTH", "nm")
    ])
    def test_GIVEN_pv_with_unit_WHEN_EGU_field_read_from_THEN_unit_returned(self, pv, expected_unit):
        self.ca.assert_that_pv_is("{pv}.EGU".format(pv=pv), expected_unit)

    @parameterized.expand([
        ("CORRELATION_FUNCTION", 400),
        ("LAGS", 400),
    ])
    def test_GIVEN_array_pv_WHEN_NELM_field_read_THEN_length_of_array_returned(self, pv, expected_length):
        self.ca.assert_that_pv_is_number("{pv}.NELM".format(pv=pv), expected_length)

    @parameterized.expand(parameterized_list(SETTING_PVS))
    def test_GIVEN_pv_name_THEN_setpoint_exists_for_that_pv(self, _, pv, value):
        self.ca.assert_setting_setpoint_sets_readback(value, pv)
    
    @parameterized.expand(parameterized_list(PV_NAMES))
    def test_GIVEN_pv_name_THEN_val_field_exists_for_that_pv(self, _, pv):
        self.ca.assert_that_pv_is("{pv}.VAL".format(pv=pv), self.ca.get_pv_value(pv))

    @parameterized.expand(parameterized_list(PV_NAMES))
    def test_GIVEN_pv_WHEN_pv_read_THEN_pv_has_no_alarms(self, _, pv):
        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)
