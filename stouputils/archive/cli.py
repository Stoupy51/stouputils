
# Imports
import os

from ..config import StouputilsConfig as Cfg
from ..print.message import debug, error, info
from .make_archive import make_archive
from .repair_zip_file import repair_zip_file


# Main entry point for command line usage
def archive_cli() -> None:
	""" Main entry point for command line usage.

	Examples:

	.. code-block:: bash

		# Repair a corrupted zip file
		python -m stouputils.archive repair /path/to/corrupted.zip /path/to/repaired.zip

		# Create a zip archive
		python -m stouputils.archive make /path/to/source /path/to/destination.zip

		# Create a zip archive with ignore patterns
		python -m stouputils.archive make /path/to/source /path/to/destination.zip --ignore "*.pyc,__pycache__"
	"""
	import argparse
	import sys

	# Check for help or no command
	if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ("--help", "-h", "help")):
		separator: str = "─" * 60
		print(f"{Cfg.CYAN}{separator}{Cfg.RESET}")
		print(f"{Cfg.CYAN}stouputils {Cfg.GREEN}archive {Cfg.CYAN}utilities{Cfg.RESET}")
		print(f"{Cfg.CYAN}{separator}{Cfg.RESET}")
		print(f"\n{Cfg.CYAN}Usage:{Cfg.RESET} stouputils archive <command> [options]")
		print(f"\n{Cfg.CYAN}Available commands:{Cfg.RESET}")
		print(f"  {Cfg.GREEN}make{Cfg.RESET} <source> <destination> [--ignore PATTERNS] [--create-dir]")
		print("      Create a zip archive from source directory")
		print(f"      {Cfg.CYAN}--ignore{Cfg.RESET}      Glob patterns to ignore (comma-separated)")
		print(f"      {Cfg.CYAN}--create-dir{Cfg.RESET}  Create destination directory if needed")
		print(f"\n  {Cfg.GREEN}repair{Cfg.RESET} <input_file> [output_file]")
		print("      Repair a corrupted zip file")
		print("      If output_file is omitted, adds '_repaired' suffix")
		print(f"{Cfg.CYAN}{separator}{Cfg.RESET}")
		return

	parser = argparse.ArgumentParser(description="Archive utilities")
	subparsers = parser.add_subparsers(dest="command", help="Available commands")

	# Repair command
	repair_parser = subparsers.add_parser("repair", help="Repair a corrupted zip file")
	repair_parser.add_argument("input_file", help="Path to the corrupted zip file")
	repair_parser.add_argument("output_file", nargs="?", help="Path to the repaired zip file (optional, defaults to input_file with '_repaired' suffix)")

	# Make archive command
	archive_parser = subparsers.add_parser("make", help="Create a zip archive")
	archive_parser.add_argument("source", help="Source directory to archive")
	archive_parser.add_argument("destination", help="Destination zip file")
	archive_parser.add_argument("--ignore", help="Glob patterns to ignore (comma-separated)")
	archive_parser.add_argument("--create-dir", action="store_true", help="Create destination directory if it doesn't exist")

	args = parser.parse_args()

	if args.command == "repair":
		input_file = args.input_file
		if args.output_file:
			output_file = args.output_file
		else:
			# Generate default output filename
			base, ext = os.path.splitext(input_file)
			output_file = f"{base}_repaired{ext}"

		debug(f"Repairing '{input_file}' to '{output_file}'...")
		try:
			repair_zip_file(input_file, output_file)
			info(f"Successfully repaired zip file: {output_file}")
		except Exception as e:
			error(f"Error repairing zip file: {e}", exit=False)
			sys.exit(1)

	elif args.command == "make":
		debug(f"Creating archive from '{args.source}' to '{args.destination}'...")
		try:
			make_archive(
				source=args.source,
				destinations=args.destination,
				create_dir=args.create_dir,
				ignore_patterns=args.ignore
			)
			info(f"Successfully created archive: {args.destination}")
		except Exception as e:
			error(f"Error creating archive: {e}", exit=False)
			sys.exit(1)

	else:
		parser.print_help()
		sys.exit(1)

