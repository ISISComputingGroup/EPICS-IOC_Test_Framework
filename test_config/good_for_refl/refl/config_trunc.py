"""
FOR TESTING

Valid configuration script for a reflectometry beamline
"""
import random
import string
from ReflectometryServer import *


RANDOM_STRING = ''.join(random.choices(string.ascii_letters + string.digits, k=5000))


def _return_random_string(*_) -> str:
    return RANDOM_STRING

def get_beamline(macros):
    """
    Returns: a beamline object describing the current beamline setup
    """
    nr = add_mode("NR")
    
    comp_0 = add_component(Component(RANDOM_STRING + "comp_0", PositionAndAngle(0.0, 2, 90)))
    add_parameter(InBeamParameter("inBeam", comp_0, description=RANDOM_STRING, custom_function=_return_random_string), modes=[nr])
    add_parameter(AxisParameter(RANDOM_STRING + "axis", comp_0, ChangeAxis.POSITION, description=RANDOM_STRING), modes=[nr])
    add_driver(IocDriver(comp_0, ChangeAxis.POSITION, MotorPVWrapper("MOT:MTR0101"), out_of_beam_positions=[OutOfBeamPosition(-2, tolerance=0.5)]))
    add_parameter(DirectParameter(RANDOM_STRING + "direct", MotorPVWrapper("MOT:MTR0101"), description=RANDOM_STRING), modes=[nr])
    add_parameter(VirtualParameter(RANDOM_STRING + "virtual", RANDOM_STRING, description=RANDOM_STRING), modes=[nr])
    add_parameter(SlitGapParameter(RANDOM_STRING + "slitGap", JawsCentrePVWrapper("MOT:JAWS1", is_vertical=True), description=RANDOM_STRING))
    add_constant(BeamlineConstant(RANDOM_STRING + "constant", RANDOM_STRING, description=RANDOM_STRING))

    add_beam_start(PositionAndAngle(0.0, 0.0, 0.0))
    return get_configured_beamline()
