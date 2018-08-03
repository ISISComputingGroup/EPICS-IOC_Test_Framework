import unittest
from hamcrest import assert_that, is_, equal_to
from ..testing import parameterized_list, add_method


class ParameterizedListTests(unittest.TestCase):

    def test_that_GIVEN_a_list_THEN_a_list_of_tuples_is_returned(self):
        # Given:
        test = [1.2, 4.6, 56]

        # When:
        result = parameterized_list(test)

        # Then:
        expected_result = [("1.2", 1.2), ("4.6", 4.6), ("56", 56)]
        assert_that(result, is_(equal_to(expected_result)))

    def test_that_GIVEN_a_list_of_tuples_with_two_objects_THEN_a_list_of_extended_tuples_is_returned(self):
        # Given:
        test = [(1.2, 'a'), (4.6, 'b'), (56, 'c')]

        # When:
        result = parameterized_list(test)

        # Then:
        expected_result = [("(1.2, 'a')", 1.2, 'a'), ("(4.6, 'b')", 4.6, 'b'), ("(56, 'c')", 56, 'c')]
        assert_that(result, is_(equal_to(expected_result)))

    def test_that_GIVEN_a_list_of_tuples_with_three_objects_THEN_a_list_of_extended_tuples_is_returned(self):
        # Given:
        test = [(1.2, 'a', [1, 3]), (4.6, 'b', [2, 4]), (56, 'c', [3, 5])]

        # When:
        result = parameterized_list(test)

        # Then:
        expected_result = [("(1.2, 'a', [1, 3])", 1.2, 'a', [1, 3]), ("(4.6, 'b', [2, 4])", 4.6, 'b', [2, 4]),
                           ("(56, 'c', [3, 5])", 56, 'c', [3, 5])]

        assert_that(result, is_(equal_to(expected_result)))

    def test_that_GIVEN_a_list_of_dictionaries__THEN_a_list_of_extended_tuples_is_returned(self):
        # Given:
        test = [{"a": 1, "b": 2}, {"a": 1, "b": 2}]

        # When:
        result = parameterized_list(test)

        # Then:
        expected_result = [("{'a': 1, 'b': 2}", {"a": 1, "b": 2}), ("{'a': 1, 'b': 2}", {"a": 1, "b": 2})]

        assert_that(result, is_(equal_to(expected_result)))


class AddMethodTests(unittest.TestCase):

    def test_that_GIVEN_a_class_decorated_with_add_method_THEN_we_can_call_the_method(self):
        # Given:
        expected_result = "hello!"

        def hello(self):
            return expected_result

        @add_method(hello)
        class Basic(object):
            pass

        # When:
        basic_instance = Basic()

        # Then
        result = basic_instance.hello()

        assert_that(result, is_(equal_to(expected_result)))


if __name__ == "__main__":
    unittest.main()
