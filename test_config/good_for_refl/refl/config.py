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


def get_beamline(macros):
    """
    Returns: a beamline object describing the current beamline setup
    """
    nr = add_mode("NR")
    polarised = add_mode("POLARISED")
    testing = add_mode("TESTING")
    disabled = add_mode("DISABLED", is_disabled=True)

    add_constant(BeamlineConstant("OPI", "SURF", "OPIs to show on front panel"))

    # S1
    z_s1 = 1 * SPACING
    add_constant(BeamlineConstant("S1_Z", z_s1, "Slit 1 z position"))
    s1_comp = add_component(Component("s1", PositionAndAngle(0.0, z_s1, 90)))
    add_parameter(AxisParameter("S1", s1_comp, ChangeAxis.POSITION), modes=[nr, polarised, testing])
    add_driver(IocDriver(s1_comp, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0101")))
    add_slit_parameters(1, modes=[nr, polarised], include_centres=True, beam_blocker="N")

    # SM
    sm_comp = add_component(ReflectingComponent("SM", PositionAndAngle(0.0, 2*SPACING, 90)))
    add_parameter(AxisParameter("SMOffset", sm_comp, ChangeAxis.POSITION), [polarised])
    add_parameter(AxisParameter("SMAngle", sm_comp, ChangeAxis.ANGLE), [polarised])
    add_parameter(InBeamParameter("SMInBeam", sm_comp), modes=[nr, polarised], mode_inits=[(polarised, True)])
    add_driver(
        IocDriver(sm_comp, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0107"), out_of_beam_positions=[SM_OUT_POS]))
    add_driver(IocDriver(sm_comp, ChangeAxis.ANGLE, MotorPVWrapper("MOT:MTR0108")))

    # THETA
    theta = add_component(ThetaComponent("ThetaComp", PositionAndAngle(0.0, 2 * SPACING, 90)))
    theta_ang = add_parameter(AxisParameter("Theta", theta, ChangeAxis.ANGLE), modes=[nr, polarised, testing])

    # S3
    s3_comp = add_component(Component("s3", PositionAndAngle(0.0, 3 * SPACING, 90)))
    add_parameter(AxisParameter("S3", s3_comp, ChangeAxis.POSITION), modes=[nr, polarised, testing])
    add_parameter(InBeamParameter("s3inbeam", s3_comp), modes=[nr, polarised, testing])
    add_driver(IocDriver(s3_comp, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0102"),
                          out_of_beam_positions=[S3_OUT_POS_LOW, S3_OUT_POS_HIGH]))

    # S4
    s4_comp = add_component(Component("s4", PositionAndAngle(0.0, 3.5 * SPACING, 90)))
    add_parameter(AxisParameter("S4", s4_comp, ChangeAxis.POSITION, autosave=True), modes=[nr, polarised, testing])
    add_driver(IocDriver(s4_comp, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0103"), synchronised=False))

    # S5
    s5_comp = add_component(Component("s5", PositionAndAngle(0.0, 3.5 * SPACING, 90)))
    add_parameter(AxisParameter("S5", s5_comp, ChangeAxis.POSITION, autosave=True), modes=[nr, polarised, testing])
    add_driver(IocDriver(s5_comp, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0206"),
                         engineering_correction=InterpolateGridDataCorrection("s4_correction.dat", theta_ang)))

    # DETECTOR
    detector = add_component(TiltingComponent("Detector", PositionAndAngle(0.0, 4*SPACING, 90)))
    add_parameter(AxisParameter("det_pos", detector, ChangeAxis.POSITION), modes=[nr, polarised, testing, disabled])
    add_parameter(AxisParameter("det_ang", detector, ChangeAxis.ANGLE), modes=[nr, polarised, disabled])
    add_driver(IocDriver(detector, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0104")))
    add_driver(IocDriver(detector, ChangeAxis.ANGLE, MotorPVWrapper("MOT:MTR0105")))
    theta.add_angle_to(detector)

    # NOT_IN_MODE
    axis_choice = add_parameter(EnumParameter("CHOICE", ["MTR0205", "MTR0207"]))
    not_in_mode_comp = add_component(Component("NotInModeComp", PositionAndAngle(0.0, 5 * SPACING, 90)))
    add_parameter(AxisParameter("notinmode", not_in_mode_comp, ChangeAxis.POSITION))
    add_driver(IocDriver(not_in_mode_comp, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0205"),
                         pv_wrapper_for_parameter=PVWrapperForParameter(axis_choice,
                                                                        {"MTR0207": MotorPVWrapper("MOT:MTR0207")})))

    # Beamline constant
    add_constant(BeamlineConstant("TEN", 10, "The value 10"))
    add_constant(BeamlineConstant("YES", True, "True is Yes"))
    add_constant(BeamlineConstant("STRING", "Test String", "A test string"))

    add_beam_start(PositionAndAngle(0.0, 0.0, 0.0))

    return get_configured_beamline()
