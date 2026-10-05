

# PYTHON_ARGCOMPLETE_OK
# Lazy imports (PEP 810), ignored before Python 3.15
from .lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import argparse
import importlib
import sys

import argcomplete

from .decorators.error_handling import handle_error

# Constants
SUBCOMMANDS: dict[str, tuple[str, str]] = {
	"archive":   ("stouputils.archive", "archive_cli"),
	"backup":    ("stouputils.backup.cli", "backup_cli"),
	"changelog": ("stouputils.continuous_delivery.git", "changelog_cli"),
	"check":     ("stouputils.check", "check_cli"),
	"redirect":  ("stouputils.io.redirect", "redirect_cli"),
}
""" Subcommands parsing their own arguments: the module holding each entry point, imported only when it runs. """

# Argument Parser Setup for Auto-Completion
parser = argparse.ArgumentParser(prog="stouputils", add_help=False)
parser.add_argument("command", nargs="?", choices=[
	"--version", "-v", "version", "show_version", "all_doctests", "archive", "backup", "build", "changelog", "check", "redirect"
])
parser.add_argument("args", nargs="*")
argcomplete.autocomplete(parser)


@handle_error(message="Error while running 'stouputils'")
def main(args: list[str] | None = None) -> None:
	if args is not None:
		sys.argv = [sys.argv[0], *args]
	second_arg: str = sys.argv[1].lower() if len(sys.argv) >= 2 else ""

	# Print the version of stouputils and its dependencies
	if second_arg in ("--version", "-v", "version", "show_version"):
		from .version_pkg import show_version_cli
		return show_version_cli()

	# Handle "all_doctests" command
	if second_arg.replace("-", "_").startswith("all_doctest"):
		root_dir: str = "." if len(sys.argv) == 2 else sys.argv[2]
		pattern: str = sys.argv[3] if len(sys.argv) >= 4 else "*"
		from .all_doctests.launch import launch_tests
		if launch_tests(root_dir, pattern=pattern) > 0:
			sys.exit(1)
		return None

	# Subcommands with their own parser see the arguments that follow their name
	if second_arg in SUBCOMMANDS:
		sys.argv.pop(1)
		module, entry_point = SUBCOMMANDS[second_arg]
		return getattr(importlib.import_module(module), entry_point)()

	# Handle "build" command
	if second_arg == "build":
		from .continuous_delivery.pypi import pypi_full_routine_using_uv
		return pypi_full_routine_using_uv()

	# Get version
	from contextlib import suppress
	from importlib.metadata import PackageNotFoundError, version
	pkg_version: str = "unknown"
	with suppress(PackageNotFoundError):
		pkg_version = version("stouputils")

	# Print help with nice formatting
	from .config import StouputilsConfig as Cfg
	separator: str = "─" * 60
	print(f"""
{Cfg.CYAN}{separator}{Cfg.RESET}
{Cfg.CYAN}stouputils {Cfg.GREEN}CLI {Cfg.CYAN}v{pkg_version}{Cfg.RESET}
{Cfg.CYAN}{separator}{Cfg.RESET}
{Cfg.CYAN}Usage:{Cfg.RESET} stouputils <command> [options]

{Cfg.CYAN}Available commands:{Cfg.RESET}
  {Cfg.GREEN}--version, -v{Cfg.RESET} [pkg] [-t <depth>]   Show version information (optionally for a specific package)
  {Cfg.GREEN}all_doctests{Cfg.RESET} [dir] [pattern]       Run all doctests in the specified directory (optionally filter by pattern)
  {Cfg.GREEN}archive{Cfg.RESET} --help                     Archive utilities (make, repair)
  {Cfg.GREEN}backup{Cfg.RESET} --help                      Backup utilities (delta, consolidate, limit)
  {Cfg.GREEN}build{Cfg.RESET} --help                       Build and publish package to PyPI using 'uv' tool (complete routine)
  {Cfg.GREEN}changelog{Cfg.RESET} --help                   Generate changelog from local git history (see --help for details)
  {Cfg.GREEN}check{Cfg.RESET} [path]...                    Report the style rules ruff cannot express (see --help for its rules)
  {Cfg.GREEN}redirect{Cfg.RESET} <src> <dst> [--help]      Move a folder and create a link at the original path
{Cfg.CYAN}{separator}{Cfg.RESET}
""".strip())
	return None

__all__ = ["main"]

if __name__ == "__main__":
	main()

