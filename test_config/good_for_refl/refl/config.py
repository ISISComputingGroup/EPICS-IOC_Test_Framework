"""
FOR TESTING

Valid configuration script for a refelctometry beamline
"""

from ReflectometryServer import *

# This is the spacing between components
SPACING = 2

# This is the position if s3 is out of the beam relative to straight through beam
S3_OUT_POSITION = -5

INIT_OUT_POSITION = -2


def get_beamline():
    """
    Returns: a beamline object describing the current beamline setup
    """
    # COMPONENTS
    s1 = Component("s1", PositionAndAngle(0.0, 1*SPACING, 90))
    s3 = Component("s3", PositionAndAngle(0.0, 3*SPACING, 90))
    detector = TiltingComponent("Detector", PositionAndAngle(0.0, 4*SPACING, 90))
    theta = ThetaComponent("ThetaComp", PositionAndAngle(0.0, 2*SPACING, 90), [detector])
    not_in_mode = Component("NotInModeComp", PositionAndAngle(0.0, 5*SPACING, 90))

    comps = [s1, theta, s3, detector, not_in_mode]

    # BEAMLINE PARAMETERS
    slit1_pos = TrackingPosition("S1", s1, True)
    slit3_pos = TrackingPosition("S3", s3, True)
    theta_ang = AngleParameter("Theta", theta, True)
    detector_position = TrackingPosition("det_pos", detector, True)
    detector_angle = AngleParameter("det_ang", detector, True)
    not_in_mode_pos = TrackingPosition("notinmode", not_in_mode, True)
    s3_enabled = InBeamParameter("s3_enabled", s3)
    hgap_param = SlitGapParameter("S1HG", JawsGapPVWrapper("MOT:JAWS1", is_vertical=False))

    params_all = [s3_enabled, slit1_pos, theta_ang, slit3_pos, detector_position, detector_angle, not_in_mode_pos, hgap_param]
    params_default = [s3_enabled, slit1_pos, theta_ang, slit3_pos, detector_position, detector_angle]
    
    params_for_mode_testing = [slit1_pos, theta_ang, slit3_pos, detector_position, s3_enabled]

    # DRIVES
    drivers = [DisplacementDriver(s1, MotorPVWrapper("MOT:MTR0101")),
               DisplacementDriver(s3, MotorPVWrapper("MOT:MTR0102"), S3_OUT_POSITION),
               DisplacementDriver(detector, MotorPVWrapper("MOT:MTR0103")),
               AngleDriver(detector, MotorPVWrapper("MOT:MTR0104")),
               # MTR0201-MTR0204 used for jaws1
               DisplacementDriver(not_in_mode, MotorPVWrapper("MOT:MTR0205"))]

    # MODES
    nr_inits = {}
    nr_mode = BeamlineMode("NR", [param.name for param in params_default], nr_inits)
    polarised_mode = BeamlineMode("POLARISED", [param.name for param in params_default], nr_inits)
    testing_mode = BeamlineMode("TESTING", [param.name for param in params_for_mode_testing], nr_inits)
    modes = [nr_mode, polarised_mode, testing_mode]

    beam_start = PositionAndAngle(0.0, 0.0, 0.0)
    bl = Beamline(comps, params_all, drivers, modes, beam_start)

    return bl
