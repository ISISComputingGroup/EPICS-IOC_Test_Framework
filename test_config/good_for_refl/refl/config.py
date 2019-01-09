# FOR TESTING
# Valid configuration script for a refelctometry beamline

from ReflectometryServer.components import *
from ReflectometryServer.geometry import *
from ReflectometryServer.beamline import Beamline, BeamlineMode
from ReflectometryServer.parameters import *
from ReflectometryServer.ioc_driver import *
from ReflectometryServer.motor_pv_wrapper import *
from ReflectometryServer.geometry import PositionAndAngle

# This is the spacing between components
SPACING = 2

# This is the position if s3 is out of the beam relative to straight through beam
OUT_POSITION = -5


def get_beamline():
    # components
    s1 = Component("s1", PositionAndAngle(0.0, 1*SPACING, 90))
    s3 = Component("s3", PositionAndAngle(0.0, 3*SPACING, 90))
    detector = TiltingComponent("Detector", PositionAndAngle(0.0, 4*SPACING, 90))
    theta = ThetaComponent("ThetaComp", PositionAndAngle(0.0, 2*SPACING, 90), [detector])
    comps = [s1, theta, s3, detector]

    # BEAMLINE PARAMETERS
    slit1_pos = TrackingPosition("S1", s1, True)
    slit3_pos = TrackingPosition("S3", s3, True)
    theta_ang = AngleParameter("Theta", theta, True)
    detector_position = TrackingPosition("det_pos", detector, True)
    detector_angle = AngleParameter("det_ang", detector, True)
    s3_enabled = InBeamParameter("s3_enabled", s3)

    params = [s3_enabled, slit1_pos, theta_ang, slit3_pos, detector_position, detector_angle]

    # DRIVES

    drivers = [DisplacementDriver(s1, MotorPVWrapper("MOT:MTR0101")),
               DisplacementDriver(s3, MotorPVWrapper("MOT:MTR0102"), OUT_POSITION),
               DisplacementDriver(detector, MotorPVWrapper("MOT:MTR0103")),
               AngleDriver(detector, MotorPVWrapper("MOT:MTR0104"))]

    # MODES
    nr_inits = {}
    nr_mode = BeamlineMode("NR", [param.name for param in params], nr_inits)
    polerised_mode = BeamlineMode("POLERISED", [param.name for param in params], nr_inits)
    modes = [nr_mode, polerised_mode]

    beam_start = PositionAndAngle(0.0, 0.0, 0.0)
    bl = Beamline(comps, params, drivers, modes, beam_start)

    return bl
