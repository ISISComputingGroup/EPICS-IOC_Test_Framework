import unittest

from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim
from common_tests.aeroflex import AeroflexCommon, DEVICE_PREFIX, EMULATOR_NAME

IOCS = [
    {
        'name': DEVICE_PREFIX,
        'directory': get_default_ioc_dir('aeroflex'),
        'macros': {
            "DEV_TYPE": "2030",
            "RF_PREC": "2"
        },
        "emulator": EMULATOR_NAME,
        "lewis_protocol": "model2030",
    },
]

TEST_MODES = [TestModes.DEVSIM]

class Aeroflex2023ATests(AeroflexCommon, unittest.TestCase):
    '''
    Tests for aeroflex model 2030. Tests inherited from AeroflexBase.
    '''
    
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0) 
        
    @parameterized.expand([('Value 1', 'AM'), ('Value 2', 'PM'), ('Value 3', 'FM')])
    @skip_if_recsim('Requires emulator logic so not supported in RECSIM')
    def test_GIVEN_new_modulation_WHEN_set_modulation_THEN_new_modulation_set(self, _, value):
        self.ca.set_pv_value('MODE:SP_NO_ACTION', value)
        self.ca.assert_that_pv_is('MODE:SP_NO_ACTION', value)
        self.ca.set_pv_value('SEND_MODE_PARAMS.PROC', 1)
        
        self.ca.assert_that_pv_is('MODE', value + '1')
        
    @parameterized.expand([('Value 1', 'FM'), ('Value 2', 'PM')])
    @skip_if_recsim('Requires emulator logic so not supported in RECSIM')
    def test_GIVEN_new_modulation_WHEN_set_modulation_with_pulse_THEN_new_modulation_set(self, _, value):
        self.ca.set_pv_value('MODE:SP_NO_ACTION', value)
        self.ca.assert_that_pv_is('MODE:SP_NO_ACTION', value)
        
        self.ca.set_pv_value('PULSE_CHECK:SP', 1)
        self.ca.assert_that_pv_is('PULSE_CHECK:SP', 'Pulse enabled')
        
        self.ca.set_pv_value('SEND_MODE_PARAMS.PROC', 1)
        
        self.ca.assert_that_pv_is('MODE', 'PULSE,' + value + '1')
        
    @skip_if_recsim('Requires emulator logic so not supported in RECSIM')
    def test_GIVEN_reset_THEN_values_are_reset(self):
        self.ca.set_pv_value('RESET', 1)
        self.ca.assert_that_pv_is('RESET', 1)
        
        self.ca.assert_that_pv_is('CARRIER_FREQ', 0)
        self.ca.assert_that_pv_is('RF_LEVEL', 0)
        self.ca.assert_that_pv_is('MODE', 'AM1')
