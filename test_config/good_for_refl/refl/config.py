# FOR TESTING
# Valid configuration script for a refelctometry beamline

from ReflectometryServer.components import *
from ReflectometryServer.geometry import *
from ReflectometryServer.beamline import Beamline, BeamlineMode
from ReflectometryServer.parameters import *
from ReflectometryServer.movement_strategy import LinearSetup
from ReflectometryServer.ioc_driver import *
from ReflectometryServer.motor_pv_wrapper import *

def get_beamline():

    s1 = Component("s1", LinearSetup(0.0, 1, 90))
    comps = [s1]

    # BEAMLINE PARAMETERS
    slit1_pos = TrackingPosition("s1", s1, True)

    params = [slit1_pos]

    # DRIVES

    drives = [
        HeightDriver(s1, MotorPVWrapper("MOT:MTR0101")),
              ]

    # MODES
    nr_inits = {}
    nr_mode = BeamlineMode("NR", ["s1"], nr_inits)
    modes = [nr_mode]

    beam_start = PositionAndAngle(0.0, 0.0, 0.0)
    bl = Beamline(comps, params, drives, modes, beam_start)

    return bl
