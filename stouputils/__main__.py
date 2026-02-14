

# PYTHON_ARGCOMPLETE_OK
# Imports
import argparse
import sys

import argcomplete

from .decorators.handle_error import handle_error

# Argument Parser Setup for Auto-Completion
parser = argparse.ArgumentParser(prog="stouputils", add_help=False)
parser.add_argument("command", nargs="?", choices=[
	"--version", "-v", "version", "show_version", "all_doctests", "archive", "backup", "build", "changelog", "redirect"
])
parser.add_argument("args", nargs="*")
argcomplete.autocomplete(parser)


@handle_error(message="Error while running 'stouputils'")
def main() -> None:
	second_arg: str = sys.argv[1].lower() if len(sys.argv) >= 2 else ""

	# Print the version of stouputils and its dependencies
	if second_arg in ("--version", "-v", "version", "show_version"):
		from .version_pkg import show_version_cli
		return show_version_cli()

	# Handle "all_doctests" command
	if second_arg.replace("-", "_").startswith("all_doctest"):
		root_dir: str = "." if len(sys.argv) == 2 else sys.argv[2]
		pattern: str = sys.argv[3] if len(sys.argv) >= 4 else "*"
		from .all_doctests import launch_tests
		if launch_tests(root_dir, pattern=pattern) > 0:
			sys.exit(1)
		return

	# Handle "archive" command
	if second_arg == "archive":
		sys.argv.pop(1)  # Remove "archive" from argv so archive_cli gets clean arguments
		from .archive import archive_cli
		return archive_cli()

	# Handle "backup" command
	if second_arg == "backup":
		sys.argv.pop(1)  # Remove "backup" from argv so backup_cli gets clean arguments
		from .backup.cli import backup_cli
		return backup_cli()

	# Handle "build" command
	if second_arg == "build":
		from .continuous_delivery.pypi import pypi_full_routine_using_uv
		return pypi_full_routine_using_uv()

	# Handle "changelog" command
	if second_arg == "changelog":
		sys.argv.pop(1)  # Remove "changelog" from argv so changelog_cli gets clean arguments
		from .continuous_delivery.git import changelog_cli
		return changelog_cli()

	# Handle "redirect" command
	if second_arg == "redirect":
		sys.argv.pop(1)  # Remove "redirect" from argv so redirect_cli gets clean arguments
		from .io.redirect import redirect_cli
		return redirect_cli()

	# Get version
	from importlib.metadata import version
	try:
		pkg_version = version("stouputils")
	except Exception:
		pkg_version = "unknown"

	# Print help with nice formatting
	from .config import StouputilsConfig as Cfg
	separator: str = "─" * 60
	print(f"""
{Cfg.CYAN}{separator}{Cfg.RESET}
{Cfg.CYAN}stouputils {Cfg.GREEN}CLI {Cfg.CYAN}v{pkg_version}{Cfg.RESET}
{Cfg.CYAN}{separator}{Cfg.RESET}
{Cfg.CYAN}Usage:{Cfg.RESET} stouputils <command> [options]

{Cfg.CYAN}Available commands:{Cfg.RESET}
  {Cfg.GREEN}--version, -v{Cfg.RESET} [pkg] [-t <depth>]    Show version information (optionally for a specific package)
  {Cfg.GREEN}all_doctests{Cfg.RESET} [dir] [pattern]        Run all doctests in the specified directory (optionally filter by pattern)
  {Cfg.GREEN}archive{Cfg.RESET} --help                      Archive utilities (make, repair)
  {Cfg.GREEN}backup{Cfg.RESET} --help                       Backup utilities (delta, consolidate, limit)
  {Cfg.GREEN}build{Cfg.RESET} [--no_stubs] [<minor|major>]  Build and publish package to PyPI using 'uv' tool (complete routine)
  {Cfg.GREEN}changelog{Cfg.RESET} [mode] [value] [options]  Generate changelog from local git history (see --help for details)
  {Cfg.GREEN}redirect{Cfg.RESET} <src> <dst> [--hardlink|--symlink]  Move a folder and create a link at the original path
{Cfg.CYAN}{separator}{Cfg.RESET}
""".strip())
	return

if __name__ == "__main__":
	main()

