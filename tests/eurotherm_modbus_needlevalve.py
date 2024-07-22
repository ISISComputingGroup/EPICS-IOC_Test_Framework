import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from utils.testing import skip_if_recsim
from utils.testing import ManagerMode, parameterized_list
from common_tests.eurotherm import EurothermBaseTests

from genie_python.genie_cachannel_wrapper import WriteAccessException

# Internal Address of device (must be 2 characters)
ADDRESS = "A01"
# Numerical address of the device
ADDR_1 = "01"  # Leave this value as 1 when changing the ADDRESS value above - hard coded in LEWIS emulator
DEVICE = "EUROTHRM_01"
NEEDLE_VALVE = "yes"
SCALING = "0.1"

EMULATOR_DEVICE = "eurotherm"

IOCS = [
    {
        "name": DEVICE,
        "directory": get_default_ioc_dir("EUROTHRM"),
        "ioc_launcher_class": ProcServLauncher,
        "macros": {
            "COMMS_MODE": "modbus",
            "NEEDLE_VALVE": "yes",
            "ADDR": ADDRESS,
            "ADDR_1": ADDR_1,
            "ADDR_2": "",
            "ADDR_3": "",
            "ADDR_4": "",
            "ADDR_5": "",
            "ADDR_6": "",
            "ADDR_7": "",
            "ADDR_8": "",
            "ADDR_9": "",
            "ADDR_10": "",
            "TEMP_SCALING_1": SCALING,
            "P_SCALING_1": "1",
            "I_SCALING_1": "1",
            "D_SCALING_1": "1",
            "OUTPUT_SCALING_1": SCALING,
        },
        "emulator": EMULATOR_DEVICE,
        "lewis_protocol": "eurotherm_modbus",
    },
    {
        # INSTETC is required to control manager mode.
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC"),
        "custom_prefix": "CS",
        "pv_for_existence": "MANAGER",
    },
]


TEST_MODES = [TestModes.DEVSIM]


class EurothermModbusNeedleValveTests(EurothermBaseTests, unittest.TestCase):
    def setUp(self):
        super(EurothermModbusNeedleValveTests, self).setUp()
        self._lewis.backdoor_set_on_device("scaling", 1.0 / float(SCALING))
        with ManagerMode(ChannelAccess()):
            self.ca.set_pv_value("A01:FLOW_SP_MODE_SELECT:SP", "AUTO")

    def get_device(self):
        return DEVICE

    def get_emulator_device(self):
        return EMULATOR_DEVICE

    def get_scaling(self):
        return SCALING

    def _get_temperature_setter_wrapper(self):
        return ManagerMode(ChannelAccess())

    # READ TESTS
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_using_needle_valve_THEN_flow_exists(self):
        self._lewis.backdoor_set_on_device("needlevalve_flow", 5.0)
        self.ca.assert_that_pv_is_number("A01:FLOW", 5.0, tolerance=0, timeout=15)

    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_using_needle_valve_THEN_valve_dir_exists(self):
        self._lewis.backdoor_set_on_device("needlevalve_direction", 1)
        self.ca.assert_that_pv_is("A01:VALVE_DIR", "OPENING", timeout=15)

    # WRITE TESTS
    @parameterized.expand(
        [
            ("A01:FLOW_SP_LOWLIM", 2.0),
            ("A01:FLOW_SP_MODE_SELECT", "MANUAL"),
            ("A01:NEEDLE_VALVE_STOP", "STOPPED"),
        ]
    )
    def test_WHEN_using_needle_valve_WHEN_SP_set_then_RBV_updates(self, pv, val):
        with ManagerMode(ChannelAccess()):
            self.ca.assert_setting_setpoint_sets_readback(value=val, readback_pv=pv, timeout=15)

    # MANAGER MODE TESTS
    @parameterized.expand(
        [
            ("A01:FLOW_SP_LOWLIM:SP", 2.0),
            ("A01:FLOW_SP_MODE_SELECT:SP", "MANUAL"),
            ("A01:NEEDLE_VALVE_STOP:SP", "STOPPED"),
        ]
    )
    def test_WHEN_using_needle_valve_WHEN_manager_mode_on_THEN_writes_allowed(self, pv, val):
        # try set with manager mode and check that it was set.
        with ManagerMode(ChannelAccess()):
            self.ca.set_pv_value(pv, val)
        self.ca.assert_that_pv_is(pv, val, timeout=15)

    @parameterized.expand([("A01:FLOW_SP_LOWLIM:SP", 2.0)])
    def test_WHEN_using_needle_valve_WHEN_manager_mode_off_THEN_writes_disallowed(self, pv, val):
        with self.assertRaises(WriteAccessException):
            self.ca.set_pv_value(pv, val)

    # SP MODE TESTS
    @parameterized.expand([("A01:TEMP:SP.DISP", "MANUAL"), ("A01:MANUAL_FLOW:SP.DISP", "AUTO")])
    def test_WHEN_using_needle_valve_THEN_sp_modes_disable_correct_PV(self, pv_disp, mode):
        with ManagerMode(ChannelAccess()):
            self.ca.set_pv_value("A01:FLOW_SP_MODE_SELECT:SP", mode)
        self.ca.assert_that_pv_is(pv_disp, "1", timeout=15)

    @parameterized.expand(
        [
            ("A01:TEMP:SP", "A01:TEMP:SP:RBV", 2.0, "AUTO"),
            ("A01:MANUAL_FLOW:SP", "A01:MANUAL_FLOW", 8.0, "MANUAL"),
        ]
    )
    def test_WHEN_using_needle_valve_and_correct_sp_mode_WHEN_manager_mode_on_THEN_writes_allowed(
        self, sp_pv, rbv_pv, val, mode
    ):
        with ManagerMode(ChannelAccess()):
            self.ca.set_pv_value("A01:FLOW_SP_MODE_SELECT:SP", mode)
            self.ca.assert_setting_setpoint_sets_readback(
                val, readback_pv=rbv_pv, set_point_pv=sp_pv, timeout=15
            )

    @parameterized.expand([("A01:TEMP:SP", 2.0, "MANUAL"), ("A01:MANUAL_FLOW:SP", 8.0, "AUTO")])
    def test_WHEN_using_needle_valve_and_incorrect_sp_mode_WHEN_manager_mode_on_THEN_writes_disallowed(
        self, pv, val, mode
    ):
        with ManagerMode(ChannelAccess()):
            self.ca.set_pv_value("A01:FLOW_SP_MODE_SELECT:SP", mode)
            with self.assertRaises(WriteAccessException):
                self.ca.set_pv_value(pv, val)

    @parameterized.expand([("A01:TEMP:SP", 2.0, "MANUAL"), ("A01:MANUAL_FLOW:SP", 8.0, "AUTO")])
    def test_WHEN_using_needle_valve_and_any_sp_mode_WHEN_manager_mode_off_THEN_writes_disallowed(
        self, pv, val, mode
    ):
        with ManagerMode(ChannelAccess()):
            self.ca.set_pv_value("A01:FLOW_SP_MODE_SELECT:SP", mode)
        with self.assertRaises(WriteAccessException):
            self.ca.set_pv_value(pv, val)

    @parameterized.expand(parameterized_list([350, 250, 1000]))
    def test_GIVEN_needle_valve_manger_mode_WHEN_temp_set_too_high_THEN_temp_capped_at_320(
        self, _, val
    ):
        adjusted_temp = val
        if val > 320:
            adjusted_temp = 320
        else:
            adjusted_temp = val
        with ManagerMode(ChannelAccess()):
            self.ca.set_pv_value("A01:TEMP:SP", val)
            self.ca.assert_that_pv_is("A01:TEMP:SP", adjusted_temp)

    @parameterized.expand(parameterized_list([40.2, 0.3, 105.6]))
    def test_GIVEN_needle_valve_manager_mode_WHEN_temp_set_THEN_scaling_is_correct(self, _, val):
        with ManagerMode(ChannelAccess()):
            self.ca.set_pv_value("A01:TEMP:SP", val)
            self.ca.assert_that_pv_is("A01:TEMP:SP", val)
