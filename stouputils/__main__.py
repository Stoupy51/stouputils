

# Imports
import sys

from .all_doctests import launch_tests
from .backup import backup_cli
from .decorators import handle_error
from .print import CYAN, GREEN, RESET, show_version


@handle_error(message="Error while running 'stouputils'")
def main() -> None:
	second_arg: str = sys.argv[1].lower() if len(sys.argv) >= 2 else ""
	if not second_arg:
		# Get version
		from importlib.metadata import version
		try:
			pkg_version = version("stouputils")
		except Exception:
			pkg_version = "unknown"

		# Print help with nice formatting
		separator: str = "─" * 60
		print(f"{CYAN}{separator}{RESET}")
		print(f"{CYAN}stouputils {GREEN}CLI {CYAN}v{pkg_version}{RESET}")
		print(f"{CYAN}{separator}{RESET}")
		print(f"\n{CYAN}Usage:{RESET} stouputils <command> [options]")
		print(f"\n{CYAN}Available commands:{RESET}")
		print(f"  {GREEN}--version, -v{RESET}       Show version information")
		print(f"  {GREEN}all_doctests{RESET} [dir]  Run all doctests in the specified directory")
		print(f"  {GREEN}backup{RESET} --help       Backup utilities (delta, consolidate, limit)")
		print(f"{CYAN}{separator}{RESET}")
		return

	# Print the version of stouputils and its dependencies
	if second_arg in ("--version","-v"):
		return show_version()

	# Handle "all_doctests" command
	if second_arg == "all_doctests":
		if launch_tests("." if len(sys.argv) == 2 else sys.argv[2]) > 0:
			sys.exit(1)
		return

	# Handle "backup" command
	if second_arg == "backup":
		sys.argv.pop(1)  # Remove "backup" from argv so backup_cli gets clean arguments
		return backup_cli()

	# Check if the command is any package name
	if second_arg in (): # type: ignore
		return


if __name__ == "__main__":
	main()

