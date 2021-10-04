# Commonly used PVs
ANGLE = "ANGLE:SP"
FREQUENCY = "FREQ:SP"
RADIUS = "RADIUS"
VELOCITY = "VEL:SP"
DISTANCE = "DIST:SP"
DISCRIMINANT = "VEL:SP:DISC:CHECK"
GALIL_ADDR = "128.0.0.0"
PREFIX = "MOT:OSCCOL"


def _custom_name_func(testcase_func, param_num, param):
    return "{}_ang_{}_freq_{}_rad_{}".format(
        testcase_func.__name__,
        *param.args[0]
    )


class OscillatingCollimatorBase(object):
    def test_WHEN_angle_set_negative_THEN_angle_is_zero(self):
        self.ca.set_pv_value(ANGLE, -1.0)
        self.ca.assert_that_pv_is_number(ANGLE, 0.0)

    def test_WHEN_angle_set_greater_than_two_THEN_angle_is_two(self):
        self.ca.set_pv_value(ANGLE, 5.0)
        self.ca.assert_that_pv_is_number(ANGLE, 2.0)

    def test_WHEN_frequency_set_negative_THEN_angle_is_zero(self):
        self.ca.set_pv_value(FREQUENCY, -1.0)
        self.ca.assert_that_pv_is_number(FREQUENCY, 0.0)

    def test_WHEN_angle_set_greater_than_half_THEN_angle_is_half(self):
        self.ca.set_pv_value(FREQUENCY, 1.0)
        self.ca.assert_that_pv_is_number(FREQUENCY, 0.5)

    def test_WHEN_frq_set_greater_than_two_THEN_angle_is_two(self):
        self.ca.set_pv_value(ANGLE, 5.0)
        self.ca.assert_that_pv_is_number(ANGLE, 2.0)

    def test_WHEN_input_values_cause_discriminant_to_be_positive_THEN_discriminant_pv_is_zero(self):

        # Act
        # in normal operations the radius is not dynamic so set it first so it is considered in future calcs
        self.ca.set_pv_value(RADIUS, 1.0)
        self.ca.set_pv_value(ANGLE, 2.0)
        self.ca.set_pv_value(FREQUENCY, 0.5)

        # Assert
        self.ca.assert_that_pv_is_number(DISCRIMINANT, 0.0)

    def test_WHEN_collimator_running_THEN_thread_is_not_on_reserved_thread(self):
        # Threads 0 and 1 are reserved for homing under IBEX
        self.ca.assert_that_pv_is_not("THREAD", "0")
        self.ca.assert_that_pv_is_not("THREAD", "1")
