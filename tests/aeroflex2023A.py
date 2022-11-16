import unittest

from parameterized import parameterized
from utils.ioc_launcher import get_default_ioc_dir
from common_tests.aeroflex import AeroflexTests, DEVICE_PREFIX, EMULATOR_NAME, TEST_MODES

IOCS = [
    {
        'name': DEVICE_PREFIX,
        'directory': get_default_ioc_dir('aeroflex'),
        'macros': {'DEV_TYPE': '2023A'},
        'emulator': EMULATOR_NAME,
        'lewis_protocol': 'model2023A',
    },
]

class Aeroflex2023ATests(AeroflexTests, unittest.TestCase):
    '''
    Tests for aeroflex model 2023A. Tests inherited from AeroflexTests.
    '''
    
    def setUp(self):
        super(Aeroflex2023ATests, self).setUp()                         

    @parameterized.expand([('Value 1', 'AM'), ('Value 2', 'AM,PM'), ('Value 3', 'AM,FM')])
    def test_GIVEN_new_modulation_WHEN_set_modulation_THEN_new_modulation_set(self, _, value):
        self.ca.set_pv_value('MODE:SP_NO_ACTION', value)
        self.ca.assert_that_pv_is('MODE:SP_NO_ACTION', value)
        self.ca.set_pv_value('SEND_MODE_PARAMS.PROC', 1)
        
        self.ca.assert_that_pv_is('MODE', value)
        
    @parameterized.expand([('Value 1', 'FM'), ('Value 2', 'PM'), ('Value 2', 'AM')])
    def test_GIVEN_new_modulation_WHEN_set_modulation_with_pulse_THEN_new_modulation_set(self, _, value):
        self.ca.set_pv_value('MODE:SP_NO_ACTION', value)
        self.ca.assert_that_pv_is('MODE:SP_NO_ACTION', value)
        
        self.ca.set_pv_value('PULSE_CHECK:SP', 1)
        self.ca.assert_that_pv_is('PULSE_CHECK:SP', 'Pulse enabled')
        
        self.ca.set_pv_value('SEND_MODE_PARAMS.PROC', 1)
        
        self.ca.assert_that_pv_is('MODE', value + ',PULSE')
        
    def test_GIVEN_reset_THEN_values_are_reset(self):
        self.ca.set_pv_value('RESET', 1)
        self.ca.assert_that_pv_is('RESET', 1)
        
        self.ca.assert_that_pv_is('CARRIER_FREQ', 0)
        self.ca.assert_that_pv_is('RF_LEVEL', 0)
        self.ca.assert_that_pv_is('MODE', 'AM')
        
    def test_GIVEN_rf_prec_set_THEN_rf_prec_is_correct(self):
        self.ca.assert_that_pv_is('RF_LEVEL.PREC', 6)
        self.ca.assert_that_pv_is('RF_LEVEL:SP.PREC', 6)
        self.ca.assert_that_pv_is('RF_LEVEL:SP_NO_ACTION.PREC', 6)
    
