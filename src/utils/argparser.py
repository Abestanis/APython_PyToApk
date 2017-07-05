import sys
from argparse import ArgumentParser


class ArgumentParserError(Exception):
    """Indicates that there was a malformed argument."""
    code = 0

    def __init__(self, code=0):
        self.code = code


class InfoActionProcessed(Exception):
    """
    This is thrown when an action was processed that
    requested the exit of the program (e.g. the --help
    or --version commands).
    """
    pass


class SubCmdArgParser(ArgumentParser):
    """
    An ArgumentParser that does not exit the interpreter
    but raises ArgumentParserError on argument errors and
    InfoActionProcessed, if the program exit was requested
    from an action.
    """

    def exit(self, status=None, message=None):
        if message:
            self._print_message(message, sys.stderr)
        if status is None:
            raise InfoActionProcessed()
        else:
            raise ArgumentParserError(status)
