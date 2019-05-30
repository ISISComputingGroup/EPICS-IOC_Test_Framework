from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
import six
import abc

UNDERLYING_GAP_SP = "MOT:JAWS{}:{}GAP:SP"
UNDERLYING_CENT_SP = "MOT:JAWS{}:{}CENT:SP"
MOD_GAP = "JAWMAN:MOD:{}GAP:SP"


@six.add_metaclass(abc.ABCMeta)
class JawsManagerBase(object):
    """
    Base classes for all jaws manager tests.
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("GALIL_01")
        ChannelAccess().assert_that_pv_exists("MOT:MTR0101", timeout=30)
        for jaw in range(1, self.get_num_of_jaws() + 1):
            ChannelAccess().assert_that_pv_exists(UNDERLYING_GAP_SP.format(jaw, "V"), timeout=30)
        self.ca = ChannelAccess()
        self.ca.assert_that_pv_exists(self.get_sample_pv() + ":{}GAP:SP".format("V"), timeout=30)

    @abc.abstractmethod
    def get_sample_pv(self):
        pass

    @abc.abstractmethod
    def get_num_of_jaws(self):
        pass

    def _test_WHEN_centre_is_changed_THEN_centres_of_all_jaws_follow_and_gaps_unchanged(self, direction):
        expected_gaps = [self.ca.get_pv_value(UNDERLYING_GAP_SP.format(jaw, direction)) for jaw in range(1, self.get_num_of_jaws() + 1)]

        self.ca.set_pv_value(self.get_sample_pv() + ":{}CENT:SP".format(direction), 10)
        for jaw in range(1, self.get_num_of_jaws() + 1):
            self.ca.assert_that_pv_is_number(UNDERLYING_CENT_SP.format(jaw, direction), 10, 0.1)
            self.ca.assert_that_pv_is_number(UNDERLYING_GAP_SP.format(jaw, direction), expected_gaps[jaw - 1], 0.1)

    def _test_WHEN_sample_gap_set_THEN_other_jaws_as_expected(self, direction, sample_gap, expected):
        self.ca.set_pv_value(self.get_sample_pv() + ":{}GAP:SP".format(direction), sample_gap)
        for i, exp in enumerate(expected):
            self.ca.assert_that_pv_is_number(UNDERLYING_GAP_SP.format(i + 1, direction), exp, 0.1)
