"""
FOR TESTING

Valid configuration script for a reflectometry beamline
"""

from ReflectometryServer import *

# This is the spacing between components
SPACING = 2

# This is the position if s3 is out of the beam relative to straight through beam
INIT_OUT_POSITION = OutOfBeamPosition(-2, tolerance=0.5)


def get_beamline(macros):
    """
    Returns: a beamline object describing the current beamline setup
    """
    nr = add_mode("NR")

    out_comp = add_component(Component("out_comp", PositionAndAngle(0.0, 1*SPACING, 90)))
    add_parameter(InBeamParameter("is_out", out_comp, autosave=False), modes=[nr])
    add_parameter(AxisParameter("out_pos", out_comp, ChangeAxis.POSITION, autosave=False), modes=[nr])
    add_driver(IocDriver(out_comp, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0101"),
                         out_of_beam_positions=[INIT_OUT_POSITION]))

    out_comp_auto = add_component(Component("out_comp_auto", PositionAndAngle(0.0, 1.5 * SPACING, 90)))
    add_parameter(InBeamParameter("is_out_auto", out_comp_auto, autosave=True), modes=[nr])
    add_driver(IocDriver(out_comp_auto, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0105"),
                         out_of_beam_positions=[INIT_OUT_POSITION]))

    in_comp = add_component(Component("in_comp", PositionAndAngle(0.0, 2*SPACING, 90)))
    add_parameter(InBeamParameter("is_in", in_comp, autosave=False), modes=[nr])
    add_parameter(AxisParameter("in_pos", in_comp, ChangeAxis.POSITION, autosave=False), modes=[nr])
    add_driver(IocDriver(in_comp, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0102"),
                         out_of_beam_positions=[INIT_OUT_POSITION]))

    theta_for_init = add_component(ThetaComponent("theta_init_comp", PositionAndAngle(0.0, 3 * SPACING, 90)))
    add_parameter(AxisParameter("theta_auto", theta_for_init, ChangeAxis.ANGLE, autosave=True), modes=[nr])

    det_for_init = add_component(TiltingComponent("det_init_comp", PositionAndAngle(0.0, 4*SPACING, 90)))
    add_parameter(AxisParameter("init", det_for_init, ChangeAxis.POSITION, autosave=False), modes=[nr])
    add_driver(IocDriver(det_for_init, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0103")))
    theta_for_init.add_angle_to(det_for_init)

    det_for_init_auto = add_component(TiltingComponent("det_init_auto_comp", PositionAndAngle(0.0, 5*SPACING, 90)))
    add_parameter(AxisParameter("init_auto", det_for_init_auto, ChangeAxis.POSITION, autosave=True), modes=[nr])
    add_driver(IocDriver(det_for_init_auto, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0104")))

    if optional_is_set(1, macros):
        add_constant(BeamlineConstant("OPTIONAL_1", "OPTIONAL_1", "Optional Beamline Constant 1"))

    if optional_is_set(2, macros):
        add_constant(BeamlineConstant("OPTIONAL_1", "OPTIONAL_1", "Optional Beamline Constant 2"))

    add_beam_start(PositionAndAngle(0.0, 0.0, 0.0))
    return get_configured_beamline()
