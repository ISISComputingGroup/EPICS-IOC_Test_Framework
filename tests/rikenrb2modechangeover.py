import os
import itertools

from common_tests.riken_changeover import RikenChangeover
from utils.ioc_launcher import get_default_ioc_dir, EPICS_TOP
from utils.test_modes import TestModes

TEST_MODES = [TestModes.RECSIM]

# Defines which IOCs talk to which power supplies.
# Key is IOC number (e.g. 1 for RKNPS_01)
# Values are a list of power supplies on this IOC.
# Only IOCs that should be switched off/interlocked should be listed here.
RIKEN_SETUP = {
    1: ["RB2"],
}


IOCS = [
    {
        "name": "COORD_01",
        "directory": get_default_ioc_dir("COORD"),
        "macros": {},
    },
    {
        "name": "SIMPLE",
        "directory": os.path.join(EPICS_TOP, "ISIS", "SimpleIoc", "master", "iocBoot", "iocsimple"),
        "macros": {},
    },
]

# Add RKNPS IOCs corresponding to RIKEN_SETUP
for ioc_num, psus in RIKEN_SETUP.iteritems():
    IOCS.append({
        "name": "RKNPS_{:02d}".format(ioc_num),
        "directory": get_default_ioc_dir("RKNPS", iocnum=ioc_num),
        "macros": dict(itertools.chain(
            # This is just a succint way of setting macros like:
            # ADR1 = 001, ADR2 = 002, ...
            # ID1 = RB1, ID2 = RB2, ... (as defined in RIKEN_SETUP above)
            {"ID{}".format(number): name for number, name in enumerate(psus, 1)}.iteritems(),
            {"ADR{}".format(number): "{:03d}".format(number) for number in range(1, len(psus) + 1)}.iteritems()
        )),
    })


# Build a list containing all the power supplies we need in a convenient form that we can easily iterate over.
POWER_SUPPLIES = []
for ioc_num, supplies in RIKEN_SETUP.iteritems():
    for supply in supplies:
        POWER_SUPPLIES.append("RKNPS_{:02d}:{}".format(ioc_num, supply))


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
