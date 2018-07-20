import argparse
import os
import sys
import unittest
import xmlrunner

from run_utils import check_test_modes, load_module, package_contents, modified_environment
from run_utils import ModuleTests

from utils.device_launcher import device_launcher, device_collection_launcher
from utils.lewis_launcher import LewisLauncher, LewisNone
from utils.ioc_launcher import IocLauncher, EPICS_TOP
from utils.free_ports import get_free_ports
from utils.test_modes import TestModes


def run_tests(prefix, test_module, test_names, device_launchers):
    """
    Runs the tests for the specified set of devices.

    :param prefix: the instrument prefix
    :param test_module: the test module
    :param test_names: tests to perform
    :param device_launchers: context manager that launches the necessary iocs and associated emulators
    """
    # Define an environment variable with the prefix in it
    # This can then be accessed elsewhere
    os.environ["testing_prefix"] = prefix

    # Need to set epics address list to local broadcast otherwise channel access won't work
    settings = {
        'EPICS_CA_ADDR_LIST': "127.255.255.255"
    }

    test_results = []

    with modified_environment(**settings), device_launchers:

        runner = xmlrunner.XMLTestRunner(output='test-reports', stream=sys.stdout)

        test_classes = [getattr(test_module, s) for s in dir(test_module) if s.endswith("Tests")]

        if len(test_classes) < 1:
            raise ValueError("No test suites found in {}".format(test_module.__name__))

        for test_class in test_classes:
            print("Running tests in {}".format(test_class.__name__))

            if test_names is not None:
                test_suite = unittest.TestSuite()
                for name in unittest.TestLoader().getTestCaseNames(test_class):
                    if name in test_names:
                        test_suite.addTest(unittest.TestLoader().loadTestsFromName(name, test_class))
            else:
                test_suite = unittest.TestLoader().loadTestsFromTestCase(test_class)

            test_results.append(runner.run(test_suite).wasSuccessful())

    return all(result is True for result in test_results)


def make_device_launchers_from_module(test_module, recsim):
    """
    Returns a list of device launchers for the given test module
    :param test_module: module containing IOC tests
    :param recsim: True to run in recsim. False to run in devsim.
    :return: list of device launchers (context managers which launch ioc + emulator pairs)
    """

    try:
        iocs = test_module.IOCS
    except AttributeError:
        raise AttributeError("Expected module '{}' to contain an IOCS attribute".format(test_module.__name__))

    if len(iocs) < 1:
        raise ValueError("Need at least one IOC to launch")

    for ioc in iocs:
        if "name" not in ioc:
            raise ValueError("IOC entry must have a 'name' attribute which should give the IOC name")
        if "directory" not in ioc:
            raise ValueError("IOC entry must have a 'directory' attribute which should give the path to the IOC")

    print("Testing module {} in {} mode.".format(test_module.__name__, "recsim" if recsim else "devsim"))

    device_launchers = []
    for ioc in iocs:

        free_port = str(get_free_ports(1)[0])
        macros = ioc.get("macros", {})
        macros['EMULATOR_PORT'] = free_port

        ioc_launcher = IocLauncher(device=ioc["name"],
                                   directory=ioc["directory"],
                                   macros=macros,
                                   use_rec_sim=recsim,
                                   var_dir=var_dir,
                                   port=free_port)

        if "emulator" in ioc and not recsim:

            emulator_device = ioc["emulator"]
            emulator_id = ioc.get("emulator_id", emulator_device)
            emulator_protocol = ioc.get("emulator_protocol", "stream")
            emulator_device_package = ioc.get("emulator_package", "lewis_emulators")
            emulator_path = ioc.get("emulator_path", os.path.join(EPICS_TOP, "support", "DeviceEmulator", "master"))

            lewis_launcher = LewisLauncher(
                device=emulator_device,
                python_path=os.path.abspath(arguments.python_path),
                lewis_path=os.path.abspath(arguments.emulator_path),
                lewis_protocol=emulator_protocol,
                lewis_additional_path=emulator_path,
                lewis_package=emulator_device_package,
                var_dir=var_dir,
                port=free_port,
                emulator_id=emulator_id
            )

        elif "emulator" in ioc:
            emulator_id = ioc.get("emulator_id", ioc["emulator"])
            lewis_launcher = LewisNone(emulator_id)
        else:
            lewis_launcher = None

        device_launchers.append(device_launcher(ioc_launcher, lewis_launcher))

    return device_launchers


def load_module_by_name_and_run_tests(module_name, test_names):
    test_module = load_module("tests.{}".format(module_name))
    modes = check_test_modes(test_module)

    test_results = []
    for mode in modes:
        if mode not in [TestModes.RECSIM, TestModes.DEVSIM]:
            raise ValueError("Invalid test mode provided")

        device_launchers = make_device_launchers_from_module(test_module, recsim=(mode == TestModes.RECSIM))
        test_results.append(run_tests(arguments.prefix, test_module, test_names, device_collection_launcher(device_launchers)))

    return all(test_result is True for test_result in test_results)


def load_and_run_dotted_tests(dotted_unit_tests):
    """
    Loads and runs the dotted unit tests to be run.

    Args:
        dotted_unit_tests: List of dotted unit tests to run.

    Returns:
        boolean: True if all tests pass and false otherwise.
    """
    modules_to_be_loaded = (test.split(".")[0].strip() for test in dotted_unit_tests)
    modules_to_be_tested = [ModuleTests(module) for module in modules_to_be_loaded]

    modes = set()

    for module in modules_to_be_tested:
        module.tests = [test for test in dotted_unit_tests if test.startswith(module.name)]
        modes.update(module.modes)

    test_results = []

    for mode in modes:
        if mode not in [TestModes.RECSIM, TestModes.DEVSIM]:
            raise ValueError("Invalid test mode provided")

        modules_to_be_tested_in_current_mode = [module for module in modules_to_be_tested if mode in module.modes]

        for module in modules_to_be_tested_in_current_mode:
            device_launchers = make_device_launchers_from_module(module.file, recsim=(mode == TestModes.RECSIM))
            test_results.append(
                run_dotted_tests(arguments.prefix, module.tests, device_collection_launcher(device_launchers)))

    return all(test_result is True for test_result in test_results)


def run_dotted_tests(prefix, dotted_unit_tests, device_launchers):
    """
    Runs dotted unit tests.

    Args:
        prefix: The instrument prefix.
        dotted_unit_tests: List of dotted unit tests to be run.
        device_launchers: Context manager that launches the necessary iocs and associated emulators.

    Returns:
        bool: True if all tests pass and false otherwise.
    """
    os.environ["testing_prefix"] = prefix

    # Need to set epics address list to local broadcast otherwise channel access won't work
    settings = {
        'EPICS_CA_ADDR_LIST': "127.255.255.255"
    }

    dotted_unit_tests = ["tests.{}".format(test) for test in dotted_unit_tests]

    with modified_environment(**settings), device_launchers:

        runner = xmlrunner.XMLTestRunner(output='test-reports', stream=sys.stdout)

        test_suite = unittest.TestLoader().loadTestsFromNames(dotted_unit_tests)

        result = runner.run(test_suite).wasSuccessful()

    return result


if __name__ == '__main__':

    pythondir = os.environ.get("PYTHONDIR", None)
    if pythondir is not None:
        emulator_path = os.path.join(pythondir, "scripts")
    else:
        emulator_path = None

    parser = argparse.ArgumentParser(
        description='Test an IOC under emulation by running tests against it')
    parser.add_argument('-l', '--list-devices',
                        help="List available devices for testing.", action="store_true")
    parser.add_argument('-pf', '--prefix', default=os.environ.get("MYPVPREFIX", None),
                        help='The instrument prefix; e.g. TE:NDW1373')
    parser.add_argument('-tm', '--test-module', default=None, nargs="+",
                        help="Test module to run")
    parser.add_argument('-e', '--emulator-path', default=emulator_path,
                        help="The path of the lewis.py file")
    parser.add_argument('-py', '--python-path', default="C:\Instrument\Apps\Python\python.exe",
                        help="The path of python.exe")
    parser.add_argument('-tn', '--test-names', default=None, type=str, nargs="+",
                        help="The names of the tests to run")
    parser.add_argument('--var-dir', default=None,
                        help="Directory in which to create a log dir to write log file to and directory in which to "
                             "create tmp dir which contains environments variables for the IOC. Defaults to "
                             "environment variable ICPVARDIR and current dir if empty.")
    parser.add_argument('-t', '--unit-tests', default=None, nargs="+",
                        help="""Dotted names of tests to run. These are of the form module.class.method. 
                        Module just runs the tests in a module. 
                        Module.class runs the the test class in Module.
                        Module.class.method runs a specific test.""")

    arguments = parser.parse_args()

    if arguments.list_devices:
        print("Available tests:")
        print('\n'.join(package_contents("tests")))
        sys.exit(0)

    var_dir = arguments.var_dir if arguments.var_dir is not None else os.getenv("ICPVARDIR", os.curdir)

    if arguments.prefix is None:
        print("Cannot run without instrument prefix")
        sys.exit(-1)

    if arguments.emulator_path is None:
        print("Cannot run without emulator path")
        sys.exit(-1)

    test_names = arguments.test_names

    unit_tests = arguments.unit_tests

    module_results = []

    modules_to_test = arguments.test_module if arguments.test_module is not None else package_contents("tests")

    if unit_tests:
        try:
            module_results.append(load_and_run_dotted_tests(unit_tests))
        except Exception as e:
            print("---\n---\n---\nError loading tests\n---\n---\n---\n")
            module_results.append(False)
    else:
        for test_module in modules_to_test:
            try:
                module_results.append(load_module_by_name_and_run_tests(test_module, test_names))
            except Exception as e:
                print("---\n---\n---\nError loading module {}: {}: {}\n---\n---\n---\n"
                      .format(test_module, e.__class__.__name__, e))
                module_results.append(False)

    success = all(result is True for result in module_results)
    sys.exit(0 if success else 1)
