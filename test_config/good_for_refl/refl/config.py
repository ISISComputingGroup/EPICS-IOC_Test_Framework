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
    nr = add_mode("NR")
    polarised = add_mode("POLARISED")
    testing = add_mode("TESTING")
    disabled = add_mode("DISABLED", is_disabled=True)

    # S1
    z_s1 = 1 * SPACING
    add_constant(BeamlineConstant("S1_Z", z_s1, "Slit 1 z position"))
    s1_comp = add_component(Component("s1", PositionAndAngle(0.0, z_s1, 90)))
    add_parameter(TrackingPosition("S1", s1_comp), modes=[nr, polarised, testing])
    add_driver(DisplacementDriver(s1_comp, MotorPVWrapper("MOT:MTR0101")))
    add_slit_parameters(1, nr, polarised)

    # SM
    sm_comp = add_component(ReflectingComponent("SM", PositionAndAngle(0.0, 2*SPACING, 90)))
    add_parameter(TrackingPosition("SMOffset", sm_comp), [polarised])
    add_parameter(AngleParameter("SMAngle", sm_comp), [polarised])
    add_parameter(InBeamParameter("SMInBeam", sm_comp), modes=[nr, polarised], mode_inits=[(polarised, True)])
    add_driver(DisplacementDriver(sm_comp, MotorPVWrapper("MOT:MTR0107"), out_of_beam_positions=[SM_OUT_POS]))
    add_driver(AngleDriver(sm_comp, MotorPVWrapper("MOT:MTR0108")))

    # THETA
    theta = add_component(ThetaComponent("ThetaComp", PositionAndAngle(0.0, 2 * SPACING, 90)))
    theta_ang = add_parameter(AngleParameter("Theta", theta, True), modes=[nr, polarised, testing])

    # S3
    s3_comp = add_component(Component("s3", PositionAndAngle(0.0, 3 * SPACING, 90)))
    add_parameter(TrackingPosition("S3", s3_comp, True), modes=[nr, polarised, testing])
    add_parameter(InBeamParameter("s3inbeam", s3_comp), modes=[nr, polarised, testing])
    add_driver(DisplacementDriver(s3_comp, MotorPVWrapper("MOT:MTR0102"), 
                                  out_of_beam_positions=[S3_OUT_POS_LOW, S3_OUT_POS_HIGH]))

    # S4
    s4_comp = add_component(Component("s4", PositionAndAngle(0.0, 3.5 * SPACING, 90)))
    add_parameter(TrackingPosition("S4", s4_comp, autosave=True), modes=[nr, polarised, testing])
    add_driver(DisplacementDriver(s4_comp, MotorPVWrapper("MOT:MTR0103"), synchronised=False))

    # S5
    s5_comp = add_component(Component("s5", PositionAndAngle(0.0, 3.5 * SPACING, 90)))
    add_parameter(TrackingPosition("S5", s5_comp, autosave=True), modes=[nr, polarised, testing])
    add_driver(DisplacementDriver(s5_comp, MotorPVWrapper("MOT:MTR0206"),
               engineering_correction=InterpolateGridDataCorrection("s4_correction.dat", theta_ang)))

    # DETECTOR
    detector = add_component(TiltingComponent("Detector", PositionAndAngle(0.0, 4*SPACING, 90)))
    add_parameter(TrackingPosition("det_pos", detector, True), modes=[nr, polarised, testing, disabled])
    add_parameter(AngleParameter("det_ang", detector, True), modes=[nr, polarised, disabled])
    add_driver(DisplacementDriver(detector, MotorPVWrapper("MOT:MTR0104")))
    add_driver(AngleDriver(detector, MotorPVWrapper("MOT:MTR0105")))

    theta.set_angle_to([detector])

    # NOT_IN_MODE
    not_in_mode_comp = add_component(Component("NotInModeComp", PositionAndAngle(0.0, 5 * SPACING, 90)))
    add_parameter(TrackingPosition("notinmode", not_in_mode_comp, True))
    add_driver(DisplacementDriver(not_in_mode_comp, MotorPVWrapper("MOT:MTR0205")))

    # Beamline constant
    add_constant(BeamlineConstant("TEN", 10, "The value 10"))
    add_constant(BeamlineConstant("YES", True, "True is Yes"))

    add_beam_start(PositionAndAngle(0.0, 0.0, 0.0))

    return get_configured_beamline()
