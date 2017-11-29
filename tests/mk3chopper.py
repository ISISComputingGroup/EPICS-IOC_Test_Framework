import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

MACROS = {"NUM_CHANNELS": 1}

class Mk3chopperTests(unittest.TestCase):

    # Remote access modes
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"
    COMP_MODE_PV = "COMP:MODE"

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("mk3chopper")
        # Comp mode is on a slow 10s read. Needs a longer timeout than default
        self.ca = ChannelAccess(device_prefix="MK3CHOPR_01", default_timeout=30)
        self.ca.wait_for(self.COMP_MODE_PV)

    def test_WHEN_ioc_is_in_remote_mode_THEN_it_has_no_alarm(self):
        # In RECSIM, switch to remote explicitly. DEVSIM can only have remote mode so no switch needed
        if IOCRegister.uses_rec_sim:
            # Bug in CA channel. Reports invalid alarm severity if you set enum directly
            self.ca.set_pv_value("SIM:{}.VAL".format(self.COMP_MODE_PV), 1)
        self.ca.assert_that_pv_is(self.COMP_MODE_PV, self.REMOTE)
        self.ca.assert_pv_alarm_is(self.COMP_MODE_PV, ChannelAccess.ALARM_NONE)

    @skipIf(not IOCRegister.uses_rec_sim, "Can't switch to local mode in DEVSIM")
    def test_WHEN_ioc_is_in_local_mode_THEN_it_has_a_major_alarm(self):
        # Bug in CA channel. Reports invalid alarm severity if you set enum directly
        self.ca.set_pv_value("SIM:{}.VAL".format(self.COMP_MODE_PV), 0)
        self.ca.assert_that_pv_is(self.COMP_MODE_PV, self.LOCAL)
        self.ca.assert_pv_alarm_is(self.COMP_MODE_PV, ChannelAccess.ALARM_MAJOR)
