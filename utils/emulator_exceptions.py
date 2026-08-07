class UnableToConnectToEmulatorException(IOError):  # noqa: N818 (historic name)
    """
    The system is unable to connect to the emulator for some reason.
    """

    def __init__(self, emulator_name: str, err: str | BaseException) -> None:
        super().__init__(f"Unable to connect to Emnulator {emulator_name}: {err}")
