import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes

DEVICE_PREFIX = "BEAMCORR_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("BEAMCORR"),
        "macros": {},
    },
]


TEST_MODES = [TestModes.RECSIM]


class BEAMCORRTests(unittest.TestCase):
    def setUp(self) -> None:

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)
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
    def test_GIVEN_musr_dir_AND_input_THEN_correct_musr_magnet(
        self, _, dir, main_val, trans_val
    ) -> None:
        self.ca.set_pv_value("SIM:MUSR_PV:MAIN", 1)
        self.ca.set_pv_value("SIM:MUSR_ROTATION", dir)

        self.ca.assert_that_pv_is("MUSR_PV:MAIN", main_val)
        self.ca.assert_that_pv_is("MUSR_PV:TRANS", trans_val)

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

    def test_GIVEN_units_set_pv_THEN_units_pushed(self) -> None:
        self.ca.set_pv_value("STEER_1:UNITS_SET", "T")
        self.ca.assert_that_pv_is("STEER_1.EGU", "T")
