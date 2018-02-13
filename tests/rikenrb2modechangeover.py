from common_tests.riken_changeover import RikenChangeover, build_iocs, build_power_supplies_list
from utils.test_modes import TestModes

TEST_MODES = [TestModes.RECSIM]

# Defines which IOCs talk to which power supplies.
# Key is IOC number (e.g. 1 for RKNPS_01)
# Values are a list of power supplies on this IOC.
# Only IOCs that should be switched off/interlocked should be listed here.
RIKEN_SETUP = {
    1: ["RB2"],
}


IOCS = build_iocs(RIKEN_SETUP)
POWER_SUPPLIES = build_power_supplies_list(RIKEN_SETUP)


class RikenRb2ModeChangeoverTests(RikenChangeover):
    """
    Tests for a riken RB2 mode change.

    Main tests are inherited from RikenChangeoverTests
    """

    def get_input_pv(self):
        return "SIMPLE:VALUE1"

    def get_acknowledgement_pv(self):
        return "SIMPLE:VALUE2"

    def get_power_supplies(self):
        return POWER_SUPPLIES

    def get_prefix(self):
        return "COORD_01:RB2C"
