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
    out_comp = Component("out_comp", PositionAndAngle(0.0, 1*SPACING, 90))
    out_comp_auto = Component("out_comp_auto", PositionAndAngle(0.0, 1.5 * SPACING, 90))
    in_comp = Component("in_comp", PositionAndAngle(0.0, 2*SPACING, 90))
    det_for_init = TiltingComponent("det_init_comp", PositionAndAngle(0.0, 4*SPACING, 90))
    det_for_init_auto = TiltingComponent("det_init_auto_comp", PositionAndAngle(0.0, 5*SPACING, 90))
    theta_for_init = ThetaComponent("theta_init_comp", PositionAndAngle(0.0, 3*SPACING, 90), [det_for_init])

    comps = [out_comp, out_comp_auto, in_comp, theta_for_init, det_for_init, det_for_init_auto]

    # BEAMLINE PARAMETERS
    is_out = InBeamParameter("is_out", out_comp, autosave=False)
    out_pos = TrackingPosition("out_pos", out_comp, autosave=False)
    is_out_auto = InBeamParameter("is_out_auto", out_comp_auto, autosave=True)
    is_in = InBeamParameter("is_in", in_comp, autosave=False)
    in_pos = TrackingPosition("in_pos", in_comp, autosave=False)
    theta_auto = AngleParameter("theta_auto", theta_for_init, autosave=True)
    init = TrackingPosition("init", det_for_init, autosave=False)
    init_auto = TrackingPosition("init_auto", det_for_init_auto, autosave=True)

    params = [is_out, out_pos, is_out_auto, is_in, in_pos, theta_auto, init, init_auto]

    # DRIVES
    drivers = [DisplacementDriver(out_comp, MotorPVWrapper("MOT:MTR0101"), INIT_OUT_POSITION, tolerance_on_out_of_beam_position=0.5),
               DisplacementDriver(out_comp_auto, MotorPVWrapper("MOT:MTR0105"), INIT_OUT_POSITION, tolerance_on_out_of_beam_position=0.5),
               DisplacementDriver(in_comp, MotorPVWrapper("MOT:MTR0102"), INIT_OUT_POSITION, tolerance_on_out_of_beam_position=0.5),
               DisplacementDriver(det_for_init, MotorPVWrapper("MOT:MTR0103")),
               DisplacementDriver(det_for_init_auto, MotorPVWrapper("MOT:MTR0104")), ]

    # MODES
    nr_inits = {}
    nr_mode = BeamlineMode("NR", [param.name for param in params], nr_inits)
    modes = [nr_mode]

    beam_start = PositionAndAngle(0.0, 0.0, 0.0)
    bl = Beamline(comps, params, drivers, modes, beam_start)

    return bl
