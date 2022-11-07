import unittest

from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

# Device prefix
DEVICE_PREFIX = "AEROFLEX_01"
EMULATOR_NAME = "aeroflex"

TEST_MODES = [TestModes.DEVSIM]

class AeroflexBase(object):
    """
    Tests for aeroflex.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0)
        
class AeroflexCommon(AeroflexBase):
    @skip_if_recsim('Requires emulator logic so not supported in RECSIM')
    def test_GIVEN_new_carrier_freq_WHEN_set_carrier_freq_THEN_new_carrier_freq_set(self):        

        self.ca.set_pv_value('CARRIER_FREQ:SP_NO_ACTION', 1.2)
        self.ca.assert_that_pv_is('CARRIER_FREQ:SP_NO_ACTION', 1.2)
        self.ca.set_pv_value('CARRIER_FREQ_UNITS:SP', 'kHZ')
        self.ca.assert_that_pv_is('CARRIER_FREQ_UNITS:SP', 'kHZ')
        self.ca.set_pv_value('SEND_CAR_FREQ_PARAMS.PROC', 1)
        
        self.ca.assert_that_pv_is('CARRIER_FREQ', 1200)
        
    @skip_if_recsim('Requires emulator logic so not supported in RECSIM')
    def test_GIVEN_carrier_freq_WHEN_set_carrier_freq_readout_units_THEN_carrier_freq_readout_changes(self): 
        self.ca.set_pv_value('CARRIER_FREQ', 1000)
        self.ca.assert_that_pv_is('CARRIER_FREQ', 1000)
        
        self.ca.set_pv_value('CARRIER_FREQ_UNITS', 'kHZ')
        self.ca.assert_that_pv_is('CARRIER_FREQ_UNITS', 'kHZ')
        self.ca.set_pv_value('CALC_RETURN_CAR_FREQ.PROC', 1)
        
        self.ca.assert_that_pv_is('CAR_FREQ_CONV', 1)

    @parameterized.expand([('Value 1', 1), ('Value 2', 2), ('Value 3', 3.33333)])
    @skip_if_recsim('Requires emulator logic so not supported in RECSIM')
    def test_GIVEN_new_rf_lvl_WHEN_set_rf_lvl_THEN_new_rf_lvl_set(self, _, value):
        self.ca.set_pv_value('RF_LEVEL:SP_NO_ACTION', value)
        self.ca.assert_that_pv_is('RF_LEVEL:SP_NO_ACTION', value)
        self.ca.set_pv_value('SEND_RF_LVL_PARAMS.PROC', 1)

        self.ca.assert_that_pv_is('RF_LEVEL', value)
        
    @skip_if_recsim('Requires emulator logic so not supported in RECSIM')
    def test_GIVEN_error_set_THEN_error_returned(self):
        self._lewis.backdoor_set_on_device('error', 'I AM ERROR')
        
        self.ca.assert_that_pv_is('ERROR', 'I AM ERROR', timeout=10)
