import unittest
from dataclasses import dataclass

from parameterized import parameterized
from itertools import product

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc, parameterized_list

# Device prefix
DEVICE_PREFIX = "HLX503_01"

# Emulator name
emulator_name = "hlx503"


@dataclass
class ITC:
    name: str
    channel : int
    isobus_address: int


# ITC503 ISOBUS addresses and channels
# Must match those in emulator device
itcs = [
    ITC("1KPOT", 1, 1), ITC("HE3POT_LOWT", 2, 2),
    ITC("HE3POT_HIGHT", 3, 3), ITC("SORB", 4, 4)
]
isobus_addresses = {f"{itc.name}_ISOBUS": itc.isobus_address for itc in itcs}
channels = {f"{itc.name}_CHANNEL": itc.channel for itc in itcs}

# Properties obtained from the get_status protocol and values to set them with
status_properties = [
    "status", "autoheat", "autoneedlevalve", "initneedlevalve", "remote",
    "locked", "sweeping", "ctrlchannel", "autopid", "tuning"
]
status_set_values = [
    8, True, True, True, True,
    True, 1, 5, True, True
]
status_expected_values = [
    8, "Auto", "Auto", "YES", "YES",
    "YES", "YES", 5, "ON", "YES"
]
status_properties_and_values = zip(status_properties, status_set_values, status_expected_values)
isobus_status_properties_and_values = product(itcs, status_properties_and_values)

# Further properties obtained from the get_status protocol and values to set them with but in combination
combo_autoheat_autoneedlevalve_initneedle_valve = [("autoheat", "autoneedlevalve", "initneedlevalve")]
combo_autoheat_autoneedlevalve_initneedle_valve_set_values = [
    (True, True, True),
    (True, False, True),
    (False, False, False),
    (True, True, False),
    (False, True, True),
]
combo_autoheat_autoneedlevalve_initneedle_valve_expected_values = [
    ("Auto", "Auto", "YES"),
    ("Auto", "Manual", "YES"),
    ("Manual", "Manual", "NO"),
    ("Auto", "Auto", "NO"),
    ("Manual", "Auto", "YES"),
]

status_combos_autoheat_autoneedlevalve_initneedle_valve = list(product(
    combo_autoheat_autoneedlevalve_initneedle_valve,
    zip(
        combo_autoheat_autoneedlevalve_initneedle_valve_set_values,
        combo_autoheat_autoneedlevalve_initneedle_valve_expected_values
    )
))

combo_remote_locked = [("remote", "locked")]
combo_remote_locked_set_values = [
    (True, True),
    (False, False),
    (True, False),
    (False, True)
]
combo_remote_locked_expected_values = [
    ("YES", "YES"),
    ("NO", "NO"),
    ("YES", "NO"),
    ("NO", "YES")
]

status_combos_remote_locked = list(product(
    combo_remote_locked,
    zip(
        combo_remote_locked_set_values,
        combo_remote_locked_expected_values
    )
))

combo_ctrlchannel_autopid_tuning = [("ctrlchannel", "autopid", "tuning")]
combo_ctrlchannel_autopid_tuning_set_values = [
    #
    (None, True, True),
    (None, False, True),
    (None, True, False),
    (None, False, False),
    #
    (None, None, None),
    (None, None, True),
    (None, None, False),
    (None, False, None),
    (None, True, None),
    #
    (5, True, True),
    (5, False, True),
    (5, True, False),
    (5, False, False),
    #
    (5, None, None),
    (5, None, True),
    (5, None, False),
    (5, False, None),
    (5, True, None),
]
combo_ctrlchannel_autopid_tuning_expected_values = [
    #
    (0, "ON", "YES"),
    (0, "OFF", "YES"),
    (0, "ON", "NO"),
    (0, "OFF", "NO"),
    #
    (0, "OFF", "NO"),
    (0, "OFF", "YES"),
    (0, "OFF", "NO"),
    (0, "OFF", "NO"),
    (0, "ON", "NO"),
    #
    (5, "ON", "YES"),
    (5, "OFF", "YES"),
    (5, "ON", "NO"),
    (5, "OFF", "NO"),
    #
    (5, "OFF", "NO"),
    (5, "OFF", "YES"),
    (5, "OFF", "NO"),
    (5, "OFF", "NO"),
    (5, "ON", "NO"),
]

status_combos_ctrlchannel_autopid_tuning = list(product(
    combo_ctrlchannel_autopid_tuning,
    zip(
        combo_ctrlchannel_autopid_tuning_set_values,
        combo_ctrlchannel_autopid_tuning_expected_values
    )
))

# Combine all the status combination test cases
itc_status_combos = list(product(
    itcs,
    status_combos_ctrlchannel_autopid_tuning +
    status_combos_remote_locked +
    status_combos_autoheat_autoneedlevalve_initneedle_valve
))


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HLX503"),
        "emulator": emulator_name,
        "macros": {**isobus_addresses, **channels}
    },
]


TEST_MODES = [TestModes.DEVSIM]


class HLX503Tests(unittest.TestCase):
    """
    Tests for the ITC503/Heliox 3He Refrigerator.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(emulator_name, DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        for itc in itcs:
            self._lewis.backdoor_run_function_on_device("reset_status", arguments=[itc.isobus_address])

    @parameterized.expand(parameterized_list(itcs))
    def test_WHEN_set_temp_via_backdoor_THEN_get_temp_value_correct(self, _, itc):
        temp = 20.0
        self._lewis.backdoor_run_function_on_device("set_temp", arguments=(itc.isobus_address, temp))
        self.ca.assert_that_pv_is(f"{itc.name}:TEMP", temp)

    @parameterized.expand(parameterized_list(isobus_status_properties_and_values))
    def test_WHEN_status_properties_set_via_backdoor_THEN_status_values_correct(self, _, itc, status_property_and_vals):
        status_property, status_set_val, status_expected_val = status_property_and_vals
        self._lewis.backdoor_run_function_on_device(f"set_{status_property}", arguments=[itc.isobus_address, status_set_val])
        self.ca.assert_that_pv_is(f"{itc.name}:{status_property.upper()}", status_expected_val)

    @parameterized.expand(parameterized_list(itc_status_combos))
    def test_WHEN_status_properties_set_in_combination_via_backdoor_THEN_status_values_correct(self, _, itc, status_property_and_vals):
        # Unpack status property and values
        properties = status_property_and_vals[0]
        set_vals = status_property_and_vals[1][0]
        expected_vals = status_property_and_vals[1][1]
        num_of_properties = len(properties)
        for i in range(num_of_properties):
            self._lewis.backdoor_run_function_on_device(f"set_{properties[i]}", arguments=[itc.isobus_address, set_vals[i]])
        for i in range(num_of_properties):
            self.ca.assert_that_pv_is(f"{itc.name}:{properties[i].upper()}", expected_vals[i])

    @parameterized.expand(parameterized_list(product(itcs, ["Auto", "Manual"])))
    def test_WHEN_set_autoheat_THEN_autoheat_set(self, _, itc, value):
        self.ca.assert_setting_setpoint_sets_readback(value, f"{itc.name}:AUTOHEAT", timeout=20)

    @parameterized.expand(parameterized_list(product(itcs, ["Auto", "Manual"])))
    def test_WHEN_set_autoneedlevalue_AND_THEN_autoneedlevalve_set(self, _, itc, value):
        self.ca.assert_setting_setpoint_sets_readback(value, f"{itc.name}:AUTONEEDLEVALVE")

    @parameterized.expand(parameterized_list(product(itcs, ["ON", "OFF"])))
    def test_WHEN_set_autopid_AND_THEN_autopid_set(self, _, itc, value):
        self.ca.assert_setting_setpoint_sets_readback(value, f"{itc.name}:AUTOPID")

    @parameterized.expand(parameterized_list(product(itcs, ["YES", "NO"])))
    def test_WHEN_set_remote_THEN_remote_set(self, _, itc, value):
        self.ca.assert_setting_setpoint_sets_readback(value, f"{itc.name}:REMOTE")

    @parameterized.expand(parameterized_list(product(itcs, ["YES", "NO"])))
    def test_WHEN_set_locked_THEN_locked_set(self, _, itc, value):
        self.ca.assert_setting_setpoint_sets_readback(value, f"{itc.name}:LOCKED")

    @parameterized.expand(parameterized_list(product(itcs, list(product(["YES", "NO"], ["YES", "NO"])))))
    def test_WHEN_set_remote_and_locked_THEN_remote_and_locked_set(self, _, itc, values):
        locked_value, remote_value = values
        self.ca.set_pv_value(f"{itc.name}:LOCKED:SP", locked_value)
        self.ca.set_pv_value(f"{itc.name}:REMOTE:SP", remote_value)
        self.ca.assert_that_pv_is(f"{itc.name}:LOCKED", locked_value)
        self.ca.assert_that_pv_is(f"{itc.name}:REMOTE", remote_value)

    @parameterized.expand(parameterized_list(product(itcs, [2.4, 18.3])))
    def test_WHEN_temp_set_THEN_temp_sp_rbv_correct(self, _, itc, value):
        self.ca.assert_setting_setpoint_sets_readback(
            value, f"{itc.name}:TEMP:SP:RBV", set_point_pv=f"{itc.name}:TEMP:SP"
        )

    @parameterized.expand(parameterized_list(product(itcs, [2.4, 18.3])))
    def test_WHEN_temp_set_THEN_temp_set(self, _, itc, value):
        self.ca.assert_setting_setpoint_sets_readback(value, f"{itc.name}:TEMP")

    @parameterized.expand(parameterized_list(product(itcs, [1, 3])))
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
        self.ca.assert_setting_setpoint_sets_readback(heater_output, f"{itc.name}:HEATER_OUTPUT")
