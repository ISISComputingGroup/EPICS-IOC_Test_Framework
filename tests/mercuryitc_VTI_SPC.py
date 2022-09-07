import contextlib
import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list, ManagerMode
import os


# These definitions should match self.channels in the emulator
TEMP_CARDS = ["MB0.T0", "DB2.T1"]
PRESSURE_CARDS = ["DB5.P0", "DB5.P1"]
LEVEL_CARDS = ["DB8.L0"]
HEATER_CARDS = ["MB1.H0", "DB3.H1", "DB6.H2"]
AUX_CARDS = ["DB1.A0", "DB4.A1", "DB7.A2"]

SPC_MIN_PRESSURE = 5.00
SPC_MAX_PRESSURE = 35.00
SPC_TEMP_DEADBAND = 2.5
SPC_GAIN = 1.5

SPC_OFFSET = 2.5
SPC_OFFSET_DURATION = 5.0 / 60.0  # make it go up 0.5 mbar a second for testing


def get_card_pv_prefix(card):
    """
    Given a card (e.g. "MB0.T1", "DB1.L1"), get the PV prefix in the IOC for it.

    Args:
        card (str): the card

    Returns:
        The pv prefix e.g. "1", "LEVEL2", "PRESSURE3"
    """
    if card in TEMP_CARDS:
        assert card not in PRESSURE_CARDS and card not in LEVEL_CARDS
        return "{}".format(TEMP_CARDS.index(card) + 1)  # Only a numeric prefix for temperature cards
    elif card in PRESSURE_CARDS:
        assert card not in LEVEL_CARDS
        return "PRESSURE:{}".format(PRESSURE_CARDS.index(card) + 1)
    elif card in LEVEL_CARDS:
        return "LEVEL:{}".format(LEVEL_CARDS.index(card) + 1)
    else:
        raise ValueError("Unknown card")


macros = {}
macros.update({"TEMP_{}".format(key): val for key, val in enumerate(TEMP_CARDS, start=1)})
macros.update({"PRESSURE_{}".format(key): val for key, val in enumerate(PRESSURE_CARDS, start=1)})
macros.update({"LEVEL_{}".format(key): val for key, val in enumerate(LEVEL_CARDS, start=1)})
macros["SPC_TYPE_1"] = "VTI"
macros["SPC_TYPE_2"] = "VTI"
macros["FLOW_SPC_PRESSURE_1"] = 1
macros["FLOW_SPC_PRESSURE_2"] = 1
macros["FLOW_SPC_MIN_PRESSURE"] = SPC_MIN_PRESSURE
macros["FLOW_SPC_TEMP_DEADBAND"] = SPC_TEMP_DEADBAND
macros["FLOW_SPC_MAX_PRESSURE"] = SPC_MAX_PRESSURE
macros["FLOW_SPC_OFFSET"] = SPC_OFFSET
macros["FLOW_SPC_OFFSET_DURATION"] = SPC_OFFSET_DURATION
macros["FLOW_SPC_GAIN"] = SPC_GAIN

macros["CALIB_BASE_DIR"] = EPICS_TOP.replace("\\", "/")
macros["CALIB_DIR"] = os.path.join("support", "mercuryitc", "master", "settings").replace("\\", "/")
macros["FLOW_SPC_TABLE_FILE"] = "little_blue_cryostat.txt"

macros["VTI_SPC_PRESSURE_1"] = 1
macros["VTI_SPC_PRESSURE_2"] = 2
macros["VTI_SPC_MIN_PRESSURE"] = 10
macros["VTI_SPC_MAX_PRESSURE"] = 50
macros["VTI_SPC_PRESSURE_CONSTANT"] = 5
macros["VTI_SPC_TEMP_CUTOFF_POINT"] = 5
macros["VTI_SPC_TEMP_SCALE"] = 5

macros["VTI_CALIB_BASE_DIR"] = "C:/Instrument/Apps/EPICS/support"
macros["VTI_SENS_DIR"] = "mercuryitc/master/test_calib/vti_spc"


DEVICE_PREFIX = "MERCURY_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(EPICS_TOP, "ioc", "master", "MERCURY_ITC", "iocBoot", "iocMERCURY-IOC-01"),
        "emulator": "mercuryitc",
        "macros": macros
    },
    {
        # INSTETC is required to enable manager mode.
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC"),
        "custom_prefix": "CS",
        "pv_for_existence": "MANAGER",
    }
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


PID_PARAMS = ["P", "I", "D"]
PID_TEST_VALUES = [0.01, 99.99]
TEMPERATURE_TEST_VALUES = [0.01, 999.9999]
RESISTANCE_TEST_VALUES = TEMPERATURE_TEST_VALUES
GAS_FLOW_TEST_VALUES = PID_TEST_VALUES
HEATER_PERCENT_TEST_VALUES = PID_TEST_VALUES
GAS_LEVEL_TEST_VALUES = PID_TEST_VALUES

PRIMARY_TEMPERATURE_CHANNEL = "MB0.T0"

HEATER_MODES = ["Auto", "Manual"]
GAS_FLOW_MODES = ["Auto", "Manual"]
AUTOPID_MODES = ["OFF", "ON"]
HELIUM_READ_RATES = ["Slow", "Fast"]

MOCK_NICKNAMES = ["MyNickName", "SomeOtherNickname"]
MOCK_CALIB_FILES = ["FakeCalib", "OtherFakeCalib", "test_calib.dat", "test space calib.dat"]

# Taken from the calibration file, minimum temperature, pressure
PRESSSURE_FOR = [(0, 35),
                 (4, 35),
                 (10, 25),
                 (20, 14),
                 (50, 10),
                 (100, 8),
                 (150, 8),
                 (200, 8),
                 (280, 8)]


def pressure_for(setpoint_temp):
    """
    For a given pressure return the base pressure
    :param setpoint_temp: set point to get pressure for
    :return: pressure
    """
    last_pressure = -10
    for temp, pressure in PRESSSURE_FOR:
        if setpoint_temp < temp:
            return last_pressure
        last_pressure = pressure
    return last_pressure


class MercuryVTISPCTests(unittest.TestCase):
    """
    Tests for the Mercury IOC VTI Software Pressure Control.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("mercuryitc", DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device("connected", True)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=20)
        self._change_spc_pressure_lookup_table("None.txt")

    def test_WHEN_ioc_started_THEN_state_machine_initialized(self):
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        self.ca.assert_that_pv_alarm_is("1:VTI_SPC:STATEMACHINE:STATE", self.ca.Alarms.NONE)

    def test_WHEN_auto_pres_ctrl_disabled_THEN_statemachine_in_init(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        self.ca.assert_that_pv_alarm_is("1:VTI_SPC:STATEMACHINE:STATUS", self.ca.Alarms.NONE)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_less_or_eq_tempsp_THEN_pressure_sp_set_to_pres_sp_minimum(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 50])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 60)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 20)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX", 50)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 20, tolerance=0.01)
        
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 20, tolerance=0.01)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_sp_less_than_cutoff_THEN_pressure_set_to_constant(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 15])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 10)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 1)
        self.ca.set_pv_value("1:VTI_SPC:TEMP:CUTOFF", 20)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:CONST", 5)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 5, tolerance=0.01)
        
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 5, tolerance=0.01)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_sp_less_than_cutoff_but_actual_temp_above_cutoff_THEN_pressure_not_set_to_constant(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 50])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 10)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 1)
        self.ca.set_pv_value("1:VTI_SPC:TEMP:CUTOFF", 15)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:CONST", 5)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 40, tolerance=0.01)
        
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 40, tolerance=0.01)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_sp_less_than_cutoff_THEN_pressure_bounded_by_minimum(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 10])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 10)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 12)
        self.ca.set_pv_value("1:VTI_SPC:TEMP:CUTOFF", 15)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:CONST", 7)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 12, tolerance=0.01)
        
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 12, tolerance=0.01)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_sp_less_than_cutoff_THEN_pressure_bounded_by_maximum(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 15])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 10)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 5)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX", 17)
        self.ca.set_pv_value("1:VTI_SPC:TEMP:CUTOFF", 15)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:CONST", 20)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 17, tolerance=0.01)
        
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 17, tolerance=0.01)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_sp_greater_than_cutoff_THEN_pressure_calculated_according_to_pressure_law(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 11])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 10)
        self.ca.set_pv_value("1:VTI_SPC:TEMP:SCALE", 2)
        self.ca.set_pv_value("1:VTI_SPC:TEMP:CUTOFF", 5)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 5)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX", 60)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:CONST", 20)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)

        # Pre-calculation: pressure_setpoint_min + temp_scale * (temperature - temperature_setpoint) ** 2
        # 5 + 2 * (15 - 10) ** 2 = 55

        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 7, tolerance=0.01)
        
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 7, tolerance=0.01)


    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_sp_greater_than_cutoff_THEN_pressure_calculated_according_to_interpolation_func(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 300])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 2)
        self.ca.set_pv_value("1:VTI_SPC:TEMP:SCALE", 2)
        self.ca.set_pv_value("1:VTI_SPC:TEMP:CUTOFF", 5)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 5)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX", 60)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:CONST", 20)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)

        # Temp      Pressure Max
        # 0         13
        # 300       13

        self.ca.assert_that_pv_is_number("1:VTI_SPC:PRESSURE:SP:MAX:LKUP", 13, tolerance=0.01)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 13, tolerance=0.01)
        
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 13, tolerance=0.01)

    def _change_spc_pressure_lookup_table(self, file_name):
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX:LKUP.NSPE", file_name)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX:LKUP.NMET", self.ca.get_pv_value("1:VTI_SPC:PRESSURE:SP:MAX:LKUP.METH"))
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX:LKUP.NBDI", self.ca.get_pv_value("1:VTI_SPC:PRESSURE:SP:MAX:LKUP.BDIR"))
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX:LKUP.NTDI", self.ca.get_pv_value("1:VTI_SPC:PRESSURE:SP:MAX:LKUP.TDIR"))
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX:LKUP.INIT", 1)
        self.ca.assert_that_pv_is("1:VTI_SPC:PRESSURE:SP:MAX:LKUP.ISTA", "Done")
        self.ca.process_pv("1:VTI_SPC:PRESSURE:SP:MAX:LKUP")

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_sp_greater_than_cutoff_THEN_pressure_calculated_according_to_complex_interpolation_func(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 250])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 2)
        self.ca.set_pv_value("1:VTI_SPC:TEMP:SCALE", 2)
        self.ca.set_pv_value("1:VTI_SPC:TEMP:CUTOFF", 5)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 5)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX", 60)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:CONST", 20)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)
        self._change_spc_pressure_lookup_table("2x1x2x.txt")

        # Temp      Pressure Max
        # 0         5
        # 100       15
        # 200       20
        # 300       30

        self.ca.process_pv("1:VTI_SPC:PRESSURE:SP:MAX:LKUP")
        self.ca.assert_that_pv_is_number("1:VTI_SPC:PRESSURE:SP:MAX:LKUP", 25, tolerance=0.01)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 25, tolerance=0.01)
        
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 25, tolerance=0.01)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 50])
        self.ca.assert_that_pv_is_number("1:VTI_SPC:PRESSURE:SP:MAX:LKUP", 10, tolerance=0.01)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_sp_min_greater_than_sp_max_THEN_statemachine_stops(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:ERROR", 0)

        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 10)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX", 20)

        self.ca.assert_that_pv_alarm_is("1:VTI_SPC:STATEMACHINE:ERROR", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:ERROR", "No errors")

        # Set up the PVs
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 20)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX", 10)
        
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "error_delay")
        self.ca.assert_that_pv_alarm_is("1:VTI_SPC:STATEMACHINE:STATE", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:ERROR", "Min Pressure > Max")
        self.ca.assert_that_pv_alarm_is("1:VTI_SPC:STATEMACHINE:ERROR", self.ca.Alarms.INVALID)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_device_disconnected_THEN_pressure_unchanged(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 50])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 60)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 20)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MAX", 50)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 20, tolerance=0.01)
        
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 20, tolerance=0.01, timeout=60)

        with self._lewis.backdoor_simulate_disconnected_device():
            self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 21)

            self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:ERROR", "Temp read failure", timeout=60)
            self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 20, tolerance=0.01)
            
        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 21, tolerance=0.01)
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:ERROR", "No errors")

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_pressure_card_invalid_THEN_statemachine_stops(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:ERROR", 0)

        self.ca.assert_that_pv_alarm_is("1:VTI_SPC:STATEMACHINE:ERROR", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:ERROR", "No errors")

        # Set up the PVs        
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE_ID", "nodevice")
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_alarm_is("1:VTI_SPC:STATEMACHINE:STATE", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:ERROR", "Invalid pressure card")
        self.ca.assert_that_pv_alarm_is("1:VTI_SPC:STATEMACHINE:ERROR", self.ca.Alarms.MINOR)

        # Put the card back how it should be.
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE_ID", PRESSURE_CARDS[0])

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_two_temp_pressure_pairs_WHEN_sm_on_for_both_THEN_setpoints_set_correctly(self):
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.set_pv_value("2:VTI_SPC:STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("1:VTI_SPC:STATEMACHINE:STATE", "init")
        self.ca.assert_that_pv_is("2:VTI_SPC:STATEMACHINE:STATE", "init")
        temp_card_pv_prefix_1 = get_card_pv_prefix(TEMP_CARDS[0])
        temp_card_pv_prefix_2 = get_card_pv_prefix(TEMP_CARDS[1])
        pressure_card_pv_prefix_1 = get_card_pv_prefix(PRESSURE_CARDS[0])
        pressure_card_pv_prefix_2 = get_card_pv_prefix(PRESSURE_CARDS[1])

        # Set up the temp card 1 PVs for the low temp loop
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 5])
        self.ca.set_pv_value(f"{temp_card_pv_prefix_1}:TEMP:SP", 10)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:SP:MIN", 1)
        self.ca.set_pv_value("1:VTI_SPC:TEMP:CUTOFF", 20)
        self.ca.set_pv_value("1:VTI_SPC:PRESSURE:CONST", 5)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix_1}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix_1}:PRESSURE:SP:RBV", 5, tolerance=0.01)

        # Set up the temp card 2 PVs for the constant set
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[1], "temperature", 15])
        self.ca.set_pv_value(f"{temp_card_pv_prefix_2}:TEMP:SP", 10)
        self.ca.set_pv_value("2:VTI_SPC:PRESSURE:SP:MIN", 1)
        self.ca.set_pv_value("2:VTI_SPC:TEMP:CUTOFF", 25)
        self.ca.set_pv_value("2:VTI_SPC:PRESSURE:CONST", 5)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix_2}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix_2}:PRESSURE:SP:RBV", 5, tolerance=0.01)

        # Start the statemachine
        
        self.ca.set_pv_value("1:VTI_SPC:STATEMACHINE:STATUS", "On")
        self.ca.set_pv_value("2:VTI_SPC:STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix_1}:PRESSURE:SP:RBV", 1, tolerance=0.01)
        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix_2}:PRESSURE:SP:RBV", 5, tolerance=0.01)
