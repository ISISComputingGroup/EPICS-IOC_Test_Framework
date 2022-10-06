import unittest
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

DEVICE_PREFIX = "TEKOSC_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TEKOSC"),
        "macros": {},
        "emulator": "tekosc",
    },
]


TEST_MODES = [TestModes.DEVSIM]


class TekOsc(unittest.TestCase):
    """
    Tests for the Tektronix Oscilloscope IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tekosc", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0, default_timeout=10)
        self._lewis.backdoor_set_on_device('connected', True)

    def test_GIVEN_nothing_WHEN_get_identity_THEN_identity_returned(self):
        identity_string = "TEKTRONIX,DPO3054,C012754,SCPI:99.0 FV:1.0"

        self.ca.assert_that_pv_is("IDN", identity_string[:39])  # limited string size

    def test_GIVEN_nothing_WHEN_curve_queried_THEN_correct_curve_returned(self):
        expected_ch1_curve = [1,1,4,2,4,3,0,3,3,3,3,3,3,4,3,5,6,6,7,3] + [0 for _ in range(9980)]
        expected_ch2_curve = [2,1,4,2,4,3,0,3,3,3,3,3,3,4,3,5,6,6,7,3] + [0 for _ in range(9980)]
        expected_ch3_curve = [3,1,4,2,4,3,0,3,3,3,3,3,3,4,3,5,6,6,7,3] + [0 for _ in range(9980)]
        expected_ch4_curve = [4,1,4,2,4,3,0,3,3,3,3,3,3,4,3,5,6,6,7,3] + [0 for _ in range(9980)]

        self.ca.assert_that_pv_is("RAWYDATA_CH1", expected_ch1_curve)
        self.ca.assert_that_pv_is("RAWYDATA_CH2", expected_ch2_curve)
        self.ca.assert_that_pv_is("RAWYDATA_CH3", expected_ch3_curve)
        self.ca.assert_that_pv_is("RAWYDATA_CH4", expected_ch4_curve)

    def test_GIVEN_nothing_when_xinc_requested_THEN_correct_unit_returned(self):
        expected_x_inc_ch1 = 3
        expected_x_inc_ch2 = 5
        expected_x_inc_ch3 = 7
        expected_x_inc_ch4 = 9

        self.ca.assert_that_pv_is("XINC_CH1", expected_x_inc_ch1)
        self.ca.assert_that_pv_is("XINC_CH2", expected_x_inc_ch2)
        self.ca.assert_that_pv_is("XINC_CH3", expected_x_inc_ch3)
        self.ca.assert_that_pv_is("XINC_CH4", expected_x_inc_ch4)

    def test_GIVEN_nothing_when_ymult_requested_THEN_correct_multiplier_returned(self):
        expected_y_mult_ch1 = 2
        expected_y_mult_ch2 = 4
        expected_y_mult_ch3 = 6
        expected_y_mult_ch4 = 8

        self.ca.assert_that_pv_is("YMULT_CH1", expected_y_mult_ch1)
        self.ca.assert_that_pv_is("YMULT_CH2", expected_y_mult_ch2)
        self.ca.assert_that_pv_is("YMULT_CH3", expected_y_mult_ch3)
        self.ca.assert_that_pv_is("YMULT_CH4", expected_y_mult_ch4)

    def test_GIVEN_nothing_when_units_requested_THEN_correct_units_returned(self):
        expected_x_unit = "s"
        expected_y_unit = "V"

        self.ca.assert_that_pv_is("XUNIT_CH1", expected_x_unit)
        self.ca.assert_that_pv_is("XUNIT_CH2", expected_x_unit)
        self.ca.assert_that_pv_is("XUNIT_CH3", expected_x_unit)
        self.ca.assert_that_pv_is("XUNIT_CH4", expected_x_unit)
        self.ca.assert_that_pv_is("YUNIT_CH1", expected_y_unit)
        self.ca.assert_that_pv_is("YUNIT_CH2", expected_y_unit)
        self.ca.assert_that_pv_is("YUNIT_CH3", expected_y_unit)
        self.ca.assert_that_pv_is("YUNIT_CH4", expected_y_unit)

    def test_GIVEN_nothing_when_xzero_requested_THEN_correct_xzeros_returned(self):
        expected_x_zero_ch1 = 12
        expected_x_zero_ch2 = 14
        expected_x_zero_ch3 = 16
        expected_x_zero_ch4 = 18

        self.ca.assert_that_pv_is("XZERO_CH1", expected_x_zero_ch1)
        self.ca.assert_that_pv_is("XZERO_CH2", expected_x_zero_ch2)
        self.ca.assert_that_pv_is("XZERO_CH3", expected_x_zero_ch3)
        self.ca.assert_that_pv_is("XZERO_CH4", expected_x_zero_ch4)

    def test_GIVEN_nothing_when_yzero_requested_THEN_correct_yzeros_returned(self):
        expected_y_zero_ch1 = 13
        expected_y_zero_ch2 = 15
        expected_y_zero_ch3 = 17
        expected_y_zero_ch4 = 19

        self.ca.assert_that_pv_is("YZERO_CH1", expected_y_zero_ch1)
        self.ca.assert_that_pv_is("YZERO_CH2", expected_y_zero_ch2)
        self.ca.assert_that_pv_is("YZERO_CH3", expected_y_zero_ch3)
        self.ca.assert_that_pv_is("YZERO_CH4", expected_y_zero_ch4)
