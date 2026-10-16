import os
import unittest

from parameterized import parameterized

from common_tests.kepco import MAX_CURRENT, emulator_name
from utils.channel_access import ChannelAccess
from utils.free_ports import get_free_ports
from utils.ioc_launcher import ProcServLauncher, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_devsim, skip_if_recsim

kepco_ports = get_free_ports(2)
DEVICE_PREFIX = "BEAMCORR_01"
HOST_PREFIX = os.environ["MYPVPREFIX"]
if not HOST_PREFIX.endswith(":"):
    HOST_PREFIX += ":"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("BEAMCORR"),
        "macros": {
            "HIFI_PV_MAIN": f"{HOST_PREFIX}KEPCO_01:CURRENT",
            "STEER_1_PV": f"{HOST_PREFIX}KEPCO_02:CURRENT",
        },
    },
    {
        "name": "KEPCO_01",
        "directory": get_default_ioc_dir("KEPCO"),
        "macros": {"CURRENT_MAX": MAX_CURRENT, "REMOTE_ON_SET": "NO"},
        "emulator": emulator_name,
        "ioc_launcher_class": ProcServLauncher,
        "device_num": "01",
    },
    {
        "name": "KEPCO_02",
        "directory": get_default_ioc_dir("KEPCO", 2),
        "macros": {"CURRENT_MAX": MAX_CURRENT, "REMOTE_ON_SET": "NO"},
        "emulator": emulator_name,
        "ioc_launcher_class": ProcServLauncher,
        "device_num": "02",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class BEAMCORRTests(unittest.TestCase):
    def setUp(self) -> None:

        self.ca = ChannelAccess(
            device_prefix=DEVICE_PREFIX, default_timeout=30, default_wait_time=0.0
        )
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)

    def tearDown(self) -> None:
        self.set_intefering_magnets(0, 0, 0, 0, 0, 0, 0)
        self.set_coefficients(0, 0, 0, 0, 0, 0, 0, 1)
        self.set_coefficients(0, 0, 0, 0, 0, 0, 0, 2)
        self.ca.set_pv_value("ENABLE:CORR", 0)

    ### When moving to super musr replace musr_dir with musr_trans
    def set_intefering_magnets(
        self, hifi_main, hifi_trans_x, hifi_trans_y, emu_main, emu_trans, musr, musr_dir
    ) -> None:
        self.ca.set_pv_value("SIM:HIFI_PV:MAIN", hifi_main)
        self.ca.set_pv_value("SIM:HIFI_PV:TRANS_X", hifi_trans_x)
        self.ca.set_pv_value("SIM:HIFI_PV:TRANS_Y", hifi_trans_y)
        self.ca.set_pv_value("SIM:EMU_PV:MAIN", emu_main)
        self.ca.set_pv_value("SIM:EMU_PV:TRANS", emu_trans)
        self.ca.set_pv_value("SIM:MUSR_PV:MAIN", musr)
        self.ca.set_pv_value("SIM:MUSR_ROTATION", musr_dir)

    def set_coefficients(
        self,
        hifi_main_coeff,
        hifi_trans_x_coeff,
        hifi_trans_y_coeff,
        emu_main_coeff,
        emu_trans_coeff,
        musr_main_coeff,
        musr_trans_coeff,
        steering_magnet,
    ) -> None:
        self.ca.set_pv_value(f"STEER_{steering_magnet}:HIFI_MAIN:COEFF", hifi_main_coeff)
        self.ca.set_pv_value(f"STEER_{steering_magnet}:HIFI_TRANS_X:COEFF", hifi_trans_x_coeff)
        self.ca.set_pv_value(f"STEER_{steering_magnet}:HIFI_TRANS_Y:COEFF", hifi_trans_y_coeff)
        self.ca.set_pv_value(f"STEER_{steering_magnet}:EMU_MAIN:COEFF", emu_main_coeff)
        self.ca.set_pv_value(f"STEER_{steering_magnet}:EMU_TRANS:COEFF", emu_trans_coeff)
        self.ca.set_pv_value(f"STEER_{steering_magnet}:MUSR_MAIN:COEFF", musr_main_coeff)
        self.ca.set_pv_value(f"STEER_{steering_magnet}:MUSR_TRANS:COEFF", musr_trans_coeff)

    @parameterized.expand(
        [
            ("_all_zero", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0),
            ("_all_one_musr_main", 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 6),
            ("_all_zero_steer2", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0),
            ("_all_one_musr_main_steer2", 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 2, 6),
            ("_all_one_musr_trans", 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6),
            ("_just_hifi_main", 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 6),
            ("_just_hifi_trans_x", 0, 0, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 6),
            ("_just_hifi_trans_y", 0, 0, 0, 0, 6, 3, 0, 0, 0, 0, 0, 0, 0, 0, 1, 18),
            ("_just_hifi_trans", 0, 0, 2, 3, 1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 1, 9),
            ("_just_emu_main", 0, 0, 0, 0, 0, 0, 2, 3, 0, 0, 0, 0, 0, 0, 1, 6),
            ("_just_emu_trans", 0, 0, 0, 0, 0, 0, 0, 0, 2, 3, 0, 0, 0, 0, 1, 6),
            ("_just_musr_main", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 3, 0, 0, 1, 6),
            ("_just_musr_main_dir_trans", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 3, 0, 1, 1, 0),
            ("_just_musr_trans_dir_main", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 3, 0, 1, 0),
            ("_just_musr_trans_dir_trans", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 3, 1, 1, 6),
            ("_just_musr_both_dir_invalid", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 3, 3, 2, 1, 0),
            ("_all_mag_no_coeff", 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0),
            ("_no_mag_all_coeff", 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0),
            ("_all_hifi", 2, 3, 4, 5, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 27),
            ("_all_emu", 0, 0, 0, 0, 0, 0, 2, 3, 4, 5, 0, 0, 0, 0, 1, 26),
            ("_all_main", 2, 3, 0, 0, 0, 0, 4, 5, 0, 0, 6, 7, 0, 0, 1, 68),
            ("_all_trans", 0, 0, 2, 3, 1, 2, 0, 0, 4, 5, 6, 0, 7, 1, 1, 70),
            ("_all_mag_no_coeff_steer2", 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0),
            ("_no_mag_all_coeff_steer2", 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0),
            ("_all_hifi_steer2", 2, 3, 4, 5, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 28),
            ("_all_emu_steer2", 0, 0, 0, 0, 0, 0, 2, 3, 4, 5, 0, 0, 0, 0, 1, 26),
            ("_all_main_steer2", 2, 3, 0, 0, 0, 0, 4, 5, 0, 0, 6, 7, 0, 0, 1, 68),
            ("_all_trans_steer2", 0, 0, 2, 3, 2, 2, 0, 0, 4, 5, 6, 0, 7, 1, 1, 72),
        ]
    )
    @skip_if_devsim("Devsim tests just to ensure remote connections.")
    def test_GIVEN_coefficients_AND_interfering_THEN_correct_offset(
        self,
        _,
        hifi_main,
        hifi_main_coeff,
        hifi_trans_x,
        hifi_trans_x_coeff,
        hifi_trans_y,
        hifi_trans_y_coeff,
        emu_main,
        emu_main_coeff,
        emu_trans,
        emu_trans_coeff,
        musr,
        musr_main_coeff,
        musr_trans_coeff,
        musr_dir,
        steering_magnet,
        offset,
    ) -> None:
        self.set_intefering_magnets(
            hifi_main, hifi_trans_x, hifi_trans_y, emu_main, emu_trans, musr, musr_dir
        )
        self.set_coefficients(
            hifi_main_coeff,
            hifi_trans_x_coeff,
            hifi_trans_y_coeff,
            emu_main_coeff,
            emu_trans_coeff,
            musr_main_coeff,
            musr_trans_coeff,
            steering_magnet,
        )

        self.ca.assert_that_pv_is(f"STEERING_{steering_magnet}:OFFSET", offset)

    @parameterized.expand(
        [
            ("MAIN", 0, 1, 0),
            (
                "TRANS",
                1,
                0,
                1,
            ),
            (
                "UNKNOWN",
                2,
                0,
                0,
            ),
        ]
    )
    @skip_if_devsim("Devsim tests just to ensure remote connections.")
    def test_GIVEN_musr_dir_AND_input_THEN_correct_musr_magnet(
        self, _, dir, main_val, trans_val
    ) -> None:
        self.ca.set_pv_value("SIM:MUSR_PV:MAIN", 1)
        self.ca.set_pv_value("SIM:MUSR_ROTATION", dir)

        self.ca.assert_that_pv_is("MUSR_PV:MAIN", main_val)
        self.ca.assert_that_pv_is("MUSR_PV:TRANS", trans_val)

    @skip_if_devsim("Devsim tests just to ensure remote connections.")
    def test_GIVEN_offset_AND_enable_corr_state_THEN_correct_output(self) -> None:
        self.set_intefering_magnets(1, 1, 1, 1, 1, 1, 0)
        self.set_coefficients(1, 1, 1, 1, 1, 1, 0, 1)
        self.ca.set_pv_value("ENABLE:CORR", 0)

        self.ca.set_pv_value("STEER_1:SP", 1)

        self.ca.assert_that_pv_is("STEER_1", 1)

        self.ca.set_pv_value("ENABLE:CORR", 1)
        self.ca.set_pv_value("STEER_1:SP", 0)

        self.ca.assert_that_pv_is("STEER_1", 6)

        self.ca.set_pv_value("ENABLE:CORR", 0)
        self.ca.assert_that_pv_is("STEER_1:SP", 6)

    @skip_if_devsim("Devsim tests just to ensure remote connections.")
    def test_GIVEN_units_set_pv_THEN_units_pushed(self) -> None:
        self.ca.set_pv_value("STEER_1:UNITS_SET", "T")
        self.ca.assert_that_pv_is("STEER_1.EGU", "T", timeout=30)

    def kepco_setup(self) -> None:
        self.kepco_1 = ChannelAccess(
            device_prefix="KEPCO_01", default_timeout=30, default_wait_time=0.0
        )
        self.kepco_1.assert_that_pv_exists("VOLTAGE", timeout=30)
        self.kepco_2 = ChannelAccess(
            device_prefix="KEPCO_02", default_timeout=30, default_wait_time=0.0
        )
        self.kepco_2.assert_that_pv_exists("VOLTAGE", timeout=30)
        self._kepco_emulator_1, self._kepco_1 = get_running_lewis_and_ioc("kepco", "KEPCO_01", "01")
        self._kepco_emulator_1.backdoor_run_function_on_device("reset")
        self._kepco_emulator_2, self._kepco_2 = get_running_lewis_and_ioc("kepco", "KEPCO_02", "02")
        self._kepco_emulator_2.backdoor_run_function_on_device("reset")

    @skip_if_recsim("Devsim setup to force connection to kepco instead of record simulation.")
    def test_GIVEN_kepco_running_AND_not_recsim_THEN_properly_reads_from_kepco(self) -> None:
        self.kepco_setup()
        self._kepco_emulator_1.backdoor_set_on_device("current", 2)
        self.ca.assert_that_pv_is("HIFI_PV:MAIN", 2)
        self.ca.set_pv_value("STEER_1:HIFI_MAIN:COEFF", 1)
        self.ca.set_pv_value("ENABLE:CORR", 1)
        self.ca.assert_that_pv_is("STEERING_1:OFFSET", 2)

    @skip_if_recsim("Devsim setup to force connection to kepco instead of record simulation.")
    def test_GIVEN_kepco_running_AND_corrections_disabled_AND_not_recsim_THEN_properly_sets_to_kepco(
        self,
    ) -> None:
        self.kepco_setup()
        self.ca.set_pv_value("ENABLE:CORR", 0)
        self.ca.set_pv_value("STEER_1:SP", 2)
        self.kepco_2.assert_that_pv_is("CURRENT:SP", 2)
        self._kepco_emulator_2.assert_that_emulator_value_is("setpoint_current", "2.0")

    @skip_if_recsim("Devsim setup to force connection to kepco instead of record simulation.")
    def test_GIVEN_kepco_running_AND_corrections_enabled_AND_not_recsim_THEN_properly_sets_to_kepco(
        self,
    ) -> None:
        self.kepco_setup()
        self.ca.set_pv_value("ENABLE:CORR", 1)
        self._kepco_emulator_1.backdoor_set_on_device("current", 2)
        self.ca.set_pv_value("STEER_1:HIFI_MAIN:COEFF", 1)
        self.ca.set_pv_value("STEER_1:SP", 2)
        self.kepco_2.assert_that_pv_is("CURRENT:SP", 4)
        self._kepco_emulator_2.assert_that_emulator_value_is("setpoint_current", "4.0")
