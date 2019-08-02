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
    s4_comp = Component("s4", PositionAndAngle(0.0, 3.5 * SPACING, 90))
    not_in_mode = Component("NotInModeComp", PositionAndAngle(0.0, 5*SPACING, 90))

    # for init tests
    out_comp = Component("out_comp", PositionAndAngle(0.0, 6*SPACING, 90))
    in_comp = Component("in_comp", PositionAndAngle(0.0, 7*SPACING, 90))
    det_for_init = TiltingComponent("det_init_comp", PositionAndAngle(0.0, 9*SPACING, 90))
    det_for_init_auto = TiltingComponent("det_init_auto_comp", PositionAndAngle(0.0, 10*SPACING, 90))
    theta_for_init = ThetaComponent("theta_init_comp", PositionAndAngle(0.0, 8*SPACING, 90), [det_for_init])

    comps = [s1, theta, s3, detector, s4_comp, not_in_mode, out_comp, in_comp, theta_for_init, det_for_init]

    # BEAMLINE PARAMETERS
    slit1_pos = TrackingPosition("S1", s1, True)
    slit3_pos = TrackingPosition("S3", s3, True)
    slit4_pos = TrackingPosition("S4", s4_comp, autosave=True)
    theta_ang = AngleParameter("Theta", theta, True)
    detector_position = TrackingPosition("det_pos", detector, True)
    detector_angle = AngleParameter("det_ang", detector, True)
    not_in_mode_pos = TrackingPosition("notinmode", not_in_mode, True)
    s3_enabled = InBeamParameter("s3_enabled", s3)
    hgap_param = SlitGapParameter("S1HG", JawsGapPVWrapper("MOT:JAWS1", is_vertical=False))

    # for init tests
    is_out = InBeamParameter("is_out", out_comp, autosave=False)
    out_pos = TrackingPosition("out_pos", out_comp, autosave=False)
    is_in = InBeamParameter("is_in", in_comp, autosave=False)
    in_pos = TrackingPosition("in_pos", in_comp, autosave=False)
    theta_auto = AngleParameter("theta_auto", theta_for_init, autosave=True)
    init = TrackingPosition("init", det_for_init, autosave=False)
    init_auto = TrackingPosition("init_auto", det_for_init_auto, autosave=True)

    params_all = [slit1_pos, s3_enabled, theta_ang, slit3_pos, detector_position, detector_angle, not_in_mode_pos,
                  is_out, out_pos, is_in, in_pos, theta_auto, init, init_auto, hgap_param, slit4_pos]

    # Do not want parameters for init tests to be moved by other tests.
    params_without_init = [s3_enabled, slit1_pos, theta_ang, slit3_pos, detector_position, detector_angle,
                           theta_auto, slit4_pos]
    
    params_for_mode_testing = [slit1_pos, theta_ang, slit3_pos, detector_position, s3_enabled]

    # DRIVES
    drivers = [DisplacementDriver(s1, MotorPVWrapper("MOT:MTR0101")),
               DisplacementDriver(s3, MotorPVWrapper("MOT:MTR0102"), S3_OUT_POSITION),
               DisplacementDriver(detector, MotorPVWrapper("MOT:MTR0103")),
               AngleDriver(detector, MotorPVWrapper("MOT:MTR0104")),
               DisplacementDriver(out_comp, MotorPVWrapper("MOT:MTR0105"), INIT_OUT_POSITION, tolerance_on_out_of_beam_position=0.5),
               DisplacementDriver(in_comp, MotorPVWrapper("MOT:MTR0106"), INIT_OUT_POSITION, tolerance_on_out_of_beam_position=0.5),
               DisplacementDriver(det_for_init, MotorPVWrapper("MOT:MTR0107")),
               DisplacementDriver(det_for_init_auto, MotorPVWrapper("MOT:MTR0108")),
               # MTR0201-MTR0204 used for jaws1
               DisplacementDriver(not_in_mode, MotorPVWrapper("MOT:MTR0205")),
               DisplacementDriver(s4_comp, MotorPVWrapper("MOT:MTR0206"),
                                  engineering_correction=InterpolateGridDataCorrection("s4_correction.dat", theta_ang))]

    # MODES
    nr_inits = {}
    nr_mode = BeamlineMode("NR", [param.name for param in params_without_init], nr_inits)
    polarised_mode = BeamlineMode("POLARISED", [param.name for param in params_without_init], nr_inits)
    testing_mode = BeamlineMode("TESTING", [param.name for param in params_for_mode_testing], nr_inits)
    modes = [nr_mode, polarised_mode, testing_mode]

    beam_start = PositionAndAngle(0.0, 0.0, 0.0)
    bl = Beamline(comps, params_all, drivers, modes, beam_start)

    return bl
