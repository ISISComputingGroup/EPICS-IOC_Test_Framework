"""
FOR TESTING

Valid configuration script for a refelctometry beamline
"""

from ReflectometryServer import *

# This is the spacing between components
SPACING = 2

# This is the position if s3 is out of the beam relative to straight through beam

SM_OUT_POS = OutOfBeamPosition(-5)
S3_OUT_POS_HIGH = OutOfBeamPosition(5)
S3_OUT_POS_LOW = OutOfBeamPosition(-5, threshold=1)


def get_beamline():
    """
    Returns: a beamline object describing the current beamline setup
    """
    # COMPONENTS
    s1 = Component("s1", PositionAndAngle(0.0, 1*SPACING, 90))
    sm_comp = ReflectingComponent("SM", PositionAndAngle(0.0, 2*SPACING, 90))
    s3 = Component("s3", PositionAndAngle(0.0, 3*SPACING, 90))
    s4_comp = Component("s4", PositionAndAngle(0.0, 3.5 * SPACING, 90))
    detector = TiltingComponent("Detector", PositionAndAngle(0.0, 4*SPACING, 90))
    theta = ThetaComponent("ThetaComp", PositionAndAngle(0.0, 2*SPACING, 90), [detector])
    s5_comp = Component("s5", PositionAndAngle(0.0, 3.5 * SPACING, 90))
    not_in_mode = Component("NotInModeComp", PositionAndAngle(0.0, 5*SPACING, 90))

    comps = [s1, sm_comp, theta, s3, s4_comp, s5_comp, detector, not_in_mode]

    # BEAMLINE PARAMETERS
    slit1_pos = TrackingPosition("S1", s1, True)
    sm_pos = TrackingPosition("SMOffset", sm_comp)
    sm_angle = AngleParameter("SMAngle", sm_comp)
    sm_in_beam = InBeamParameter("SMInBeam", sm_comp)
    slit3_pos = TrackingPosition("S3", s3, True)
    slit4_pos = TrackingPosition("S4", s4_comp, autosave=True)
    slit5_pos = TrackingPosition("S5", s5_comp, autosave=True)

    theta_ang = AngleParameter("Theta", theta, True)
    detector_position = TrackingPosition("det_pos", detector, True)
    detector_angle = AngleParameter("det_ang", detector, True)
    not_in_mode_pos = TrackingPosition("notinmode", not_in_mode, True)
    s3_enabled = InBeamParameter("s3inbeam", s3)
    hgap_param = SlitGapParameter("S1HG", JawsGapPVWrapper("MOT:JAWS1", is_vertical=False))
    hcentre_param = SlitGapParameter("S1HC", JawsCentrePVWrapper("MOT:JAWS1", is_vertical=False))
    vgap_param = SlitGapParameter("S1VG", JawsGapPVWrapper("MOT:JAWS1", is_vertical=True))
    vcentre_param = SlitGapParameter("S1VC", JawsCentrePVWrapper("MOT:JAWS1", is_vertical=True))

    params_all = [slit1_pos, sm_in_beam, sm_pos, sm_angle, s3_enabled, theta_ang, slit3_pos, detector_position,
                  detector_angle, not_in_mode_pos, hgap_param, vgap_param, hcentre_param, vcentre_param, slit4_pos, slit5_pos]
    params_polerised = [slit1_pos, sm_in_beam, sm_pos, sm_angle, s3_enabled, theta_ang, slit3_pos, detector_position,
                  detector_angle, hgap_param, vgap_param, hcentre_param, vcentre_param, slit4_pos, slit5_pos]
    params_nr = [slit1_pos, s3_enabled, theta_ang, slit3_pos, detector_position, detector_angle,
                 hgap_param, vgap_param, hcentre_param, vcentre_param, slit4_pos, slit5_pos]

    params_for_mode_testing = [slit1_pos, theta_ang, slit3_pos, slit4_pos, slit5_pos, detector_position, s3_enabled]
    params_for_mode_disabled = [detector_position, detector_angle]

    # DRIVES
    drivers = [DisplacementDriver(s1, MotorPVWrapper("MOT:MTR0101")),
               DisplacementDriver(s3, MotorPVWrapper("MOT:MTR0102"), out_of_beam_positions=[S3_OUT_POS_LOW, S3_OUT_POS_HIGH]),
               DisplacementDriver(s4_comp, MotorPVWrapper("MOT:MTR0103"), synchronised=False),
               DisplacementDriver(detector, MotorPVWrapper("MOT:MTR0104")),
               AngleDriver(detector, MotorPVWrapper("MOT:MTR0105")),
               DisplacementDriver(sm_comp, MotorPVWrapper("MOT:MTR0107"), out_of_beam_positions=[SM_OUT_POS]),
               AngleDriver(sm_comp, MotorPVWrapper("MOT:MTR0108")),
               # MTR0201-MTR0204 used for jaws1
               DisplacementDriver(not_in_mode, MotorPVWrapper("MOT:MTR0205")),
               DisplacementDriver(s5_comp, MotorPVWrapper("MOT:MTR0206"),
                                  engineering_correction=InterpolateGridDataCorrection("s4_correction.dat", theta_ang))]

    # MODES
    nr_inits = {sm_in_beam.name: False}
    polarised_inits = {sm_in_beam.name: True}
    nr_mode = BeamlineMode("NR", [param.name for param in params_nr], nr_inits)
    polarised_mode = BeamlineMode("POLARISED", [param.name for param in params_polerised], polarised_inits)
    testing_mode = BeamlineMode("TESTING", [param.name for param in params_for_mode_testing], {})
    disabled_mode = BeamlineMode("DISABLED", [param.name for param in params_for_mode_disabled], {}, is_disabled=True)
    modes = [nr_mode, polarised_mode, testing_mode, disabled_mode]

    # Value parameters
    value_parameters = [
        BeamlineConstant("TEN", 10, "The value 10"),
        BeamlineConstant("YES", True, "True is Yes")]

    beam_start = PositionAndAngle(0.0, 0.0, 0.0)
    bl = Beamline(comps, params_all, drivers, modes, beam_start, beamline_constants=value_parameters)

    return bl
