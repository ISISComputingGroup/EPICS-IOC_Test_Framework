import importlib
import os
from contextlib import contextmanager


def package_contents(package_path):
    """
    Finds all the files in a package.

    :param package_path: the name of the package
    :return: a set containing all the module names
    """
    return set([os.path.splitext(module)[0] for module in os.listdir(package_path)
                if module.endswith('.py') and not module.startswith("__init__")])


@contextmanager
def modified_environment(**kwargs):
    """
    Modifies the environment variables as required then returns them to their original state.

    :param kwargs: the settings to apply
    """
    # Copying old values
    old_env = {name: os.environ.get(name, '') for name in kwargs.keys()}

    # Apply new settings and then yield
    os.environ.update(kwargs)
    yield

    # Restore old values
    os.environ.update(old_env)


class ModuleTests(object):
    """
    Object which contains information about tests in a module to be run.

    Attributes:
        name: Name of the module where the tests are.
        tests: List of "dotted" test names. E.g. SampleTests.SampleTestCase.test_two runs
            test_two in SampleTestCase class in the SampleTests module.
        file: Reference to the module.
        modes: Modes to run the tests in.
    """

    def __init__(self, name):
        self.__name = name
        self.tests = None
        self.__file = self.__get_file_reference()
        self.__modes = self.__get_modes()

    @property
    def name(self):
        """ Returns the name of the module."""
        return self.__name

    @property
    def modes(self):
        """ Returns the modes to run the tests in. """
        return self.__modes

    @property
    def file(self):
        """ Returns a reference to the module file. """
        return self.__file

    def __get_file_reference(self):
        module = load_module("tests.{}".format(self.__name))
        return module

    def __get_modes(self):
        if not self.__file:
            self.__get_file_reference()
        return check_test_modes(self.__file)


def load_module(name):
    """
    Loads a module based on its name.

    :param name: the name of the module
    :return: a reference to the module
    """
    return importlib.import_module(name, )


def check_test_modes(module):
    """
    Checks for RECSIM and DEVSIM test modes.

    :param module: Modules to check for RECSIM and DEVSIM test modes
    :return: set: Modes that the tests can be run in.
    """
    try:
        modes = set(module.TEST_MODES)
    except AttributeError:
        raise ValueError("Expected test module {} to contain a TEST_MODES attribute".format(module.__name__))

    return modes


