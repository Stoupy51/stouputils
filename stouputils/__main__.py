

# PYTHON_ARGCOMPLETE_OK
# Imports
import argparse
import sys

import argcomplete

from .all_doctests import launch_tests
from .archive import archive_cli
from .backup import backup_cli
from .decorators import handle_error
from .print import CYAN, GREEN, RESET
from .version_pkg import show_version_cli

# Argument Parser Setup for Auto-Completion
parser = argparse.ArgumentParser(prog="stouputils", add_help=False)
parser.add_argument("command", nargs="?", choices=[
	"--version", "-v", "version", "show_version", "all_doctests", "archive", "backup", "build"
])
parser.add_argument("args", nargs="*")
argcomplete.autocomplete(parser)


@handle_error(message="Error while running 'stouputils'")
def main() -> None:
	second_arg: str = sys.argv[1].lower() if len(sys.argv) >= 2 else ""

	# Print the version of stouputils and its dependencies
	if second_arg in ("--version", "-v", "version", "show_version"):
		return show_version_cli()

	# Handle "all_doctests" command
	if second_arg == "all_doctests":
		if launch_tests("." if len(sys.argv) == 2 else sys.argv[2]) > 0:
			sys.exit(1)
		return

	# Handle "archive" command
	if second_arg == "archive":
		sys.argv.pop(1)  # Remove "archive" from argv so archive_cli gets clean arguments
		return archive_cli()

	# Handle "backup" command
	if second_arg == "backup":
		sys.argv.pop(1)  # Remove "backup" from argv so backup_cli gets clean arguments
		return backup_cli()

	# Handle "build" command
	if second_arg == "build":
		from .continuous_delivery.pypi import pypi_full_routine_using_uv
		return pypi_full_routine_using_uv()

	# Check if the command is any package name
	if second_arg in (): # type: ignore
		return

	# Get version
	from importlib.metadata import version
	try:
		pkg_version = version("stouputils")
	except Exception:
		pkg_version = "unknown"

	# Print help with nice formatting
	separator: str = "─" * 60
	print(f"""
{CYAN}{separator}{RESET}
{CYAN}stouputils {GREEN}CLI {CYAN}v{pkg_version}{RESET}
{CYAN}{separator}{RESET}
{CYAN}Usage:{RESET} stouputils <command> [options]

{CYAN}Available commands:{RESET}
  {GREEN}--version, -v{RESET} [pkg] [-t <depth>]    Show version information (optionally for a specific package)
  {GREEN}all_doctests{RESET} [dir]                  Run all doctests in the specified directory
  {GREEN}archive{RESET} --help                      Archive utilities (make, repair)
  {GREEN}backup{RESET} --help                       Backup utilities (delta, consolidate, limit)
  {GREEN}build{RESET} [--no_stubs] [<minor|major>]  Build and publish package to PyPI using 'uv' tool (complete routine)
{CYAN}{separator}{RESET}
""".strip())
	return

if __name__ == "__main__":
	main()

