
# Imports
from ..config import StouputilsConfig as Cfg
from .consolidate import consolidate_backups
from .create import create_delta_backup
from .limiter import limit_backups


# Main entry point for command line usage
def backup_cli() -> None:
	""" Main entry point for command line usage.

	Examples:

	.. code-block:: bash

		# Create a delta backup, excluding libraries and cache folders
		python -m stouputils.backup delta /path/to/source /path/to/backups -x "libraries/*" "cache/*"

		# Consolidate backups into a single file
		python -m stouputils.backup consolidate /path/to/backups/latest.zip /path/to/consolidated.zip

		# Limit the number of delta backups to 5
		python -m stouputils.backup limit 5 /path/to/backups
	"""
	import argparse
	import sys

	# Check for help or no command
	if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ("--help", "-h", "help")):
		separator: str = "─" * 60
		print(f"{Cfg.CYAN}{separator}{Cfg.RESET}")
		print(f"{Cfg.CYAN}Backup Utilities{Cfg.RESET}")
		print(f"{Cfg.CYAN}{separator}{Cfg.RESET}")
		print(f"\n{Cfg.CYAN}Usage:{Cfg.RESET} stouputils backup <command> [options]")
		print(f"\n{Cfg.CYAN}Available commands:{Cfg.RESET}")
		print(f"  {Cfg.GREEN}delta{Cfg.RESET}         Create a new delta backup")
		print(f"  {Cfg.GREEN}consolidate{Cfg.RESET}   Consolidate existing backups into one")
		print(f"  {Cfg.GREEN}limit{Cfg.RESET}         Limit the number of delta backups")
		print(f"\n{Cfg.CYAN}For detailed help on a specific command:{Cfg.RESET}")
		print("  stouputils backup <command> --help")
		print(f"{Cfg.CYAN}{separator}{Cfg.RESET}")
		return

	# Setup command line argument parser
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		description="Backup and consolidate files using delta compression.",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=f"""{Cfg.CYAN}Examples:{Cfg.RESET}
  stouputils backup delta /path/to/source /path/to/backups -x "*.pyc"
  stouputils backup consolidate /path/to/backups/latest.zip /path/to/output.zip
  stouputils backup limit 5 /path/to/backups"""
	)
	subparsers = parser.add_subparsers(dest="command", required=False)

	# Create delta command and its arguments
	delta_psr = subparsers.add_parser("delta", help="Create a new delta backup")
	delta_psr.add_argument("source", type=str, help="Path to the source directory or file")
	delta_psr.add_argument("destination", type=str, help="Path to the destination folder for backups")
	delta_psr.add_argument("-x", "--exclude", type=str, nargs="+", help="Glob patterns to exclude from backup", default=[])

	# Create consolidate command and its arguments
	consolidate_psr = subparsers.add_parser("consolidate", help="Consolidate existing backups into one")
	consolidate_psr.add_argument("backup_zip", type=str, help="Path to the latest backup ZIP file")
	consolidate_psr.add_argument("destination_zip", type=str, help="Path to the destination consolidated ZIP file")

	# Create limit command and its arguments
	limit_psr = subparsers.add_parser("limit", help="Limit the number of delta backups by consolidating the oldest ones")
	limit_psr.add_argument("max_backups", type=int, help="Maximum number of delta backups to keep")
	limit_psr.add_argument("backup_folder", type=str, help="Path to the folder containing backups")
	limit_psr.add_argument("--no-keep-oldest", dest="keep_oldest", action="store_false", default=True, help="Allow deletion of the oldest backup (default: keep it)")

	# Parse arguments and execute appropriate command
	args: argparse.Namespace = parser.parse_args()


	if args.command == "delta":
		create_delta_backup(args.source, args.destination, args.exclude)
	elif args.command == "consolidate":
		consolidate_backups(args.backup_zip, args.destination_zip)
	elif args.command == "limit":
		limit_backups(args.max_backups, args.backup_folder, keep_oldest=args.keep_oldest)

