import unittest

from utils.build_architectures import BuildArchitectures
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import skip_if_devsim

DEVICE_PREFIX = "MK3CHOPR_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MK3CHOPR"),
        "macros": {"NUM_CHANNELS": 1},
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]
# VISA not yet available on 32 bit
BUILD_ARCHITECTURES = [BuildArchitectures._64BIT]


class Mk3chopperTests(unittest.TestCase):
    # Remote access modes
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"
    COMP_MODE_PV = "COMP:MODE"

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        # Comp mode is on a slow 10s read. Needs a longer timeout than default
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)
        self.ca.assert_that_pv_exists(self.COMP_MODE_PV)

    def test_WHEN_ioc_is_in_remote_mode_THEN_it_has_no_alarm(self):
        # In RECSIM, switch to remote explicitly. DEVSIM can only have remote mode so no switch needed
        if IOCRegister.uses_rec_sim:
            # Bug in CA channel. Reports invalid alarm severity if you set enum directly
            self.ca.set_pv_value("SIM:{}.VAL".format(self.COMP_MODE_PV), 1)
        self.ca.assert_that_pv_is(self.COMP_MODE_PV, self.REMOTE)
        self.ca.assert_that_pv_alarm_is(self.COMP_MODE_PV, ChannelAccess.Alarms.NONE)

    @skip_if_devsim("Can't switch to local mode in DEVSIM")
    def test_WHEN_ioc_is_in_local_mode_THEN_it_has_a_major_alarm(self):
        # Bug in CA channel. Reports invalid alarm severity if you set enum directly
        self.ca.set_pv_value("SIM:{}.VAL".format(self.COMP_MODE_PV), 0)
        self.ca.assert_that_pv_is(self.COMP_MODE_PV, self.LOCAL)
        self.ca.assert_that_pv_alarm_is(self.COMP_MODE_PV, ChannelAccess.Alarms.MAJOR)
