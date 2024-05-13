import os
import unittest

from time import sleep
from hamcrest import assert_that, is_, equal_to, has_length

from ..emulator_launcher import CommandLineEmulatorLauncher


class TestEmulatorLauncher(unittest.TestCase):
    def test_that_GIVEN_a_commandline_emulator_opens_THEN_it_closes_properly(self):
        emulator = (
            CommandLineEmulatorLauncher("test_that_GIVEN_a_commandline_emulator_opens_THEN_it_closes_properly",
                                        "commandline_emulator",
                                        "commandline_test.bat",
                                        "",
                                        "",
                                    {"emulator_command_line":"cmd.exe"}))
        emulator._open()
        assert_that(emulator._process.is_running(), is_(equal_to(True)))
        sleep(1)  # Time for any subprocesses to open
        assert_that(emulator._process.children(recursive=True), is_(has_length(1)))
        emulator._close()
        assert_that(emulator._process.is_running(), is_(equal_to(False)))
        assert_that(emulator._process.children(recursive=True), is_(equal_to([])))

    def test_that_GIVEN_a_commandline_emulator_opens_AND_has_child_proceses_THEN_all_closes_properly(self):
        emulator = (
            CommandLineEmulatorLauncher("test_that_GIVEN_a_commandline_emulator_opens_THEN_it_closes_properly",
                                        "commandline_emulator",
                                        os.path.join(os.getcwd(),"utils","tests"),
                                        "",
                                        "",
                                        {"emulator_command_line": "cmd.exe /c commandline_test.bat",
                                            "emulator_cwd_emulator_path": True}))
        emulator._open()
        assert_that(emulator._process.is_running(), is_(equal_to(True)))
        sleep(1)  # Time for any subprocesses to open
        assert_that(emulator._process.children(recursive=True), has_length(5))
        emulator._close()
        assert_that(emulator._process.is_running(), is_(equal_to(False)))
        assert_that(emulator._process.children(recursive=True), is_(equal_to([])))

    def test_that_GIVEN_a_commandline_emulator_opens_AND_has_nested_child_proceses_THEN_all_closes_properly(self):
        emulator = (
            CommandLineEmulatorLauncher("test_that_GIVEN_a_commandline_emulator_opens_THEN_it_closes_properly",
                                        "commandline_emulator",
                                        os.path.join(os.getcwd(),"utils","tests"),
                                        "",
                                        "",
                                        {"emulator_command_line": "cmd.exe /c commandline_nested_test.bat",
                                            "emulator_cwd_emulator_path": True}))
        emulator._open()
        assert_that(emulator._process.is_running(), is_(equal_to(True)))
        sleep(1)  # Time for any subprocesses to open
        assert_that(emulator._process.children(recursive=True), has_length(7))
        emulator._close()
        assert_that(emulator._process.is_running(), is_(equal_to(False)))
        assert_that(emulator._process.children(recursive=True), is_(equal_to([])))


if __name__ == "__main__":
    unittest.main()
