import argparse
import sys
from collections.abc import Sequence
from typing import override

CLI_DESCRIPTION = "CLI to interstitial journal."

LICENSE_TEXT = """
    ============================== LICENSE =======================================

    MIT License

    Copyright (c) 2026 arlecchino

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

    ==============================================================================
"""


class LicenseAction(argparse.Action):
    """
    Define Action for flag -l and --license.
    """

    @override
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        print(LICENSE_TEXT)
        parser.exit()


def create_arg_parser() -> argparse.ArgumentParser:
    """
    Create and return the CLI Argument Parser.
    """

    parser = argparse.ArgumentParser(
        prog="jlog",
        description=CLI_DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    _ = parser.add_argument(
        "-l",
        "--license",
        action=LicenseAction,
        nargs=0,
        help="Show license information and exit",
    )
    verbosity_group = parser.add_mutually_exclusive_group()
    _ = verbosity_group.add_argument("-q", "--quiet", help="Use quiet output", action="store_true")
    _ = verbosity_group.add_argument("-v", "--verbose", help="Use verbose output", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """
    Run the jlog command-line interface.

    This function is executed when you type `jlog` or `python -m jlog`.
    """

    parser = create_arg_parser()
    parsed_args = parser.parse_args(args=argv)

    # The following distinction is needed for testing:
    # - main() tests normal process behavior.
    # - main([]) tests deliberately running with no arguments.
    # - main(["--help"]) tests a specific argument sequence without changing global state.
    #   This is a common dependency-injection technique - command-line input is passed into the function instead of always being read from global state.
    arguments = list(argv) if argv is not None else sys.argv[1:]

    if not arguments:
        parser.print_help()
        return 0

    return 0
