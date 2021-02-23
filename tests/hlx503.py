import unittest
from dataclasses import dataclass
from typing import Any

from parameterized import parameterized
from itertools import product

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc, parameterized_list
from utils.free_ports import get_free_ports
from utils.emulator_launcher import TestEmulatorData

# Device prefix
DEVICE_PREFIX = "HLX503_01"

# Must match those in emulator device
@dataclass
class ITC503:
    name: str
    port: str
    launcher_address: int
    emulator_port: Any


ports = get_free_ports(4)
itcs = [
    ITC503("1KPOT", "COM1", 0, ports[0]), ITC503("HE3POT_LOWT", "COM2", 1, ports[1]),
    ITC503("HE3POT_HIGHT", "COM3", 2, ports[2]), ITC503("SORB", "COM4", 3, ports[3])
]
itc_ports = {f"{itc503.name}_PORT": itc503.port for itc503 in itcs}
itc_emulator_ports = {f"{itc503.name}_EMULATOR_PORT": itc503.emulator_port for itc503 in itcs}


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HLX503"),
        "emulators": [TestEmulatorData("itc503", itc503.emulator_port, itc503.launcher_address) for itc503 in itcs],
        "macros": {**itc_ports, **itc_emulator_ports}
    },
]


TEST_MODES = [TestModes.DEVSIM]


class HLX503Tests(unittest.TestCase):
    """
    Tests for the ITC503/Heliox 3He Refrigerator.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tests.hlx503", DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    @parameterized.expand(parameterized_list(product(itcs, ["Auto", "Manual"])))
    def test_WHEN_set_autoheat_THEN_autoheat_set(self, _, itc, value):
        self.ca.assert_setting_setpoint_sets_readback(value, f"{itc.name}:MODE:HTR")

    @parameterized.expand(parameterized_list(product(itcs, ["Auto", "Manual"])))
    def test_WHEN_set_autoneedlevalue_AND_THEN_autoneedlevalve_set(self, _, itc, value):
        self.ca.assert_setting_setpoint_sets_readback(value, f"{itc.name}:MODE:GAS")

    @parameterized.expand(parameterized_list(product(itcs, ["ON", "OFF"])))
    def test_WHEN_set_autopid_AND_THEN_autopid_set(self, _, itc, value):
        self.ca.assert_setting_setpoint_sets_readback(value, f"{itc.name}:AUTOPID")

    @parameterized.expand(parameterized_list(product(itcs, ["Locked", "Remote only", "Local only", "Local and remote"])))
    def test_WHEN_set_remote_THEN_remote_set(self, _, itc, value):
        expected_alarm = self.ca.Alarms.NONE if value != "Local only" else self.ca.Alarms.MAJOR
        self.ca.assert_setting_setpoint_sets_readback(value, f"{itc.name}:CTRL", expected_alarm=expected_alarm)

    @parameterized.expand(parameterized_list(product(itcs, [2.4, 18.3])))
    def test_WHEN_temp_set_THEN_temp_sp_rbv_correct(self, _, itc, val):
        self.ca.set_pv_value(f"{itc.name}:TEMP:SP", val)
        self.ca.assert_that_pv_is_number(f"{itc.name}:TEMP:SP:RBV", val, tolerance=0.1)
        self.ca.assert_that_pv_is_number(f"{itc.name}:TEMP:1", val, tolerance=0.1)
        self.ca.assert_that_pv_is_number(f"{itc.name}:TEMP:2", val, tolerance=0.1)
        self.ca.assert_that_pv_is_number(f"{itc.name}:TEMP:3", val, tolerance=0.1)

    @parameterized.expand(parameterized_list(product(itcs, ["Channel 1", "Channel 2", "Channel 3"])))
    def test_WHEN_ctrlchannel_set_THEN_ctrlchannel_set(self, _, itc, new_control_channel):
        self.ca.assert_setting_setpoint_sets_readback(new_control_channel, f"{itc.name}:CTRLCHANNEL")

    @parameterized.expand(parameterized_list(product(itcs, [0.2, 3.8])))
    def test_WHEN_proportional_set_THEN_proportional_set(self, _, itc, proportional):
        self.ca.assert_setting_setpoint_sets_readback(proportional, f"{itc.name}:P")

    @parameterized.expand(parameterized_list(product(itcs, [0.2, 3.8])))
    def test_WHEN_integral_set_THEN_integral_set(self, _, itc, integral):
        self.ca.assert_setting_setpoint_sets_readback(integral, f"{itc.name}:I")

    @parameterized.expand(parameterized_list(product(itcs, [0.2, 3.8])))
    def test_WHEN_derivative_set_THEN_derivative_set(self, _, itc, derivative):
        self.ca.assert_setting_setpoint_sets_readback(derivative, f"{itc.name}:D")

    @parameterized.expand(parameterized_list(product(itcs, [23.2, 87.1])))
    def test_WHEN_heater_output_set_THEN_heater_output_set(self, _, itc, heater_output):
        self.ca.assert_setting_setpoint_sets_readback(heater_output, f"{itc.name}:HEATERP")

    @parameterized.expand(parameterized_list(product(itcs, [31.9, 66.6])))
    def test_WHEN_gasflow_set_THEN_gasflow_set(self, _, itc, percent):
        self.ca.assert_setting_setpoint_sets_readback(percent, f"{itc.name}:GASFLOW")
