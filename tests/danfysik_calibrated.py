import unittest

from common_tests.danfysik import DEVICE_PREFIX, EMULATOR_NAME, DanfysikCommon
from utils.ioc_launcher import ProcServLauncher, get_default_ioc_dir
from utils.test_modes import TestModes

# write factor = 10 * (1 / read factor)
read_scale_factor = 0.5
write_scale_factor = 20
max_raw_setpoint = 500000

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DFKPS"),
        "macros": {
            "DEV_TYPE": "8000",
            "CALIBRATED": "1",
            "FACTOR_READ_I": read_scale_factor,
            "FACTOR_READ_V": "1",
            "FACTOR_WRITE_I": write_scale_factor,
            "MAX_RAW_SETPOINT": max_raw_setpoint,
            "DISABLE_AUTOONOFF": "0",
            "SP_AT_STARTUP": "NO",
        },
        "emulator": EMULATOR_NAME,
        "lewis_protocol": "model8000",
        "pv_for_existence": "FIELD",
        "ioc_launcher_class": ProcServLauncher,
    },
]

# RECSIM does not read / write raw values at different scales
TEST_MODES = [TestModes.DEVSIM]


class DanfysikCalibratedTests(DanfysikCommon, unittest.TestCase):
    """
    Tests for a calibrated danfysik with asymmetric read/write factors. Tests inherited from DanfysikBase.
    """

    def setUp(self):
        super().setUp()
        self.current_readback_factor = read_scale_factor
        self.ca.set_pv_value("FIELD:SP", 0)
        self._lewis.backdoor_run_function_on_device("set_current_read_factor", [read_scale_factor])
        self._lewis.backdoor_run_function_on_device(
            "set_current_write_factor", [write_scale_factor]
        )

    def test_GIVEN_asymmetric_read_and_write_WHEN_setting_current_THEN_current_rbv_and_sp_rbv_are_correct(
        self,
    ):
        expected = 100
        for id_prefix in self.id_prefixes:
            self.ca.set_pv_value(f"{id_prefix}CURR:SP", expected)

            self.ca.assert_that_pv_is_number(f"{id_prefix}CURR", expected)
            self.ca.assert_that_pv_is_number(f"{id_prefix}CURR:SP:RBV", expected)

    def test_GIVEN_asymmetric_read_and_write_WHEN_setting_field_THEN_rbv_and_sp_rbv_and_percent_are_correct(
        self,
    ):
        # default scaling field:raw is 1:1
        expected = 10000
        expected_percent = 100.0 / max_raw_setpoint * expected
        for id_prefix in self.id_prefixes:
            self.ca.set_pv_value(f"{id_prefix}FIELD:SP", expected)

            self.ca.assert_that_pv_is_number(f"{id_prefix}FIELD", expected)
            self.ca.assert_that_pv_is_number(f"{id_prefix}FIELD:SP:RBV", expected)
            self.ca.assert_that_pv_is_number(f"{id_prefix}RAW:PERCENT", expected_percent)

    def test_GIVEN_asymmetric_read_and_write_WHEN_setting_field_THEN_curr_is_correct(self):
        # default scaling field:raw is 1:1
        field_to_set = 10000
        expected = field_to_set / write_scale_factor
        for id_prefix in self.id_prefixes:
            self.ca.set_pv_value(f"{id_prefix}FIELD:SP", field_to_set)

            self.ca.assert_that_pv_is_number(f"{id_prefix}CURR", expected)
