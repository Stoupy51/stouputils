
# Imports
import os
import shutil

from ..config import StouputilsConfig as Cfg
from .path import clean_path


# Functions
def is_junction(path: str) -> bool:
	""" Check if a path is a junction point (Windows) or a symlink (any OS).

	Args:
		path (str): The path to check
	Returns:
		bool: True if the path is a junction or symlink
	"""
	if os.path.islink(path):
		return True
	try:
		return os.path.isjunction(path)
	except AttributeError:
		# Python < 3.12 fallback for Windows junctions
		if os.name != "nt":
			return False
		import ctypes
		FILE_ATTRIBUTE_REPARSE_POINT = 0x400
		attrs = ctypes.windll.kernel32.GetFileAttributesW(path)  # type: ignore[union-attr]
		return attrs != -1 and bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)

def create_junction(source: str, target: str) -> None:
	""" Create a directory junction on Windows pointing source -> target.
	Uses 'mklink /J' command.

	Args:
		source (str): The junction path to create (with forward slashes, will be converted)
		target (str): The target directory the junction points to
	"""
	import subprocess
	# mklink requires backslashes on Windows
	src_win = source.replace("/", "\\")
	tgt_win = target.replace("/", "\\")
	result = subprocess.run(
		["cmd", "/c", "mklink", "/J", src_win, tgt_win],
		capture_output=True, text=True
	)
	if result.returncode != 0:
		raise OSError(f"Failed to create junction: {result.stderr.strip()}")

def create_bind_mount(source: str, target: str) -> None:
	""" Create a bind mount on Linux pointing source -> target.
	Uses ``mount --bind`` command (requires root/sudo).

	Note:
		Bind mounts do **not** persist across reboots unless an entry is added to ``/etc/fstab``.
		To make it persistent, add this line to ``/etc/fstab``::

			/absolute/path/to/target /absolute/path/to/source none bind 0 0

	Args:
		source (str): The mount point path to create (must exist as an empty directory)
		target (str): The target directory to bind
	Raises:
		:py:exc:`OSError`: If the bind mount command fails
	"""
	import subprocess
	result = subprocess.run(
		["sudo", "mount", "--bind", target, source],
		capture_output=True, text=True
	)
	if result.returncode != 0:
		raise OSError(f"Failed to create bind mount: {result.stderr.strip()}")

def copytree_with_progress(
	source: str,
	destination: str,
	desc: str = "Copying",
) -> str:
	""" Copy a directory tree from source to destination with a colored progress bar.

	Uses :func:`~stouputils.print.progress_bar.colored_for_loop` to display progress while copying each file.
	Directory structure is created automatically. Existing files at the destination are overwritten.

	Args:
		source		(str):	Path to the source directory to copy
		destination	(str):	Path to the destination directory
		desc		(str):	Description for the progress bar (default: ``"Copying"``)
	Returns:
		str:	The destination path
	Raises:
		:py:exc:`NotADirectoryError`: If source is not a directory

	Examples:

		.. code-block:: python

			> copytree_with_progress("C:/Games/MyGame", "D:/Backup/MyGame")
			# Copying: 100%|██████████████████| 150/150 [00:05<00:00, 30.00it/s]
			'D:/Backup/MyGame'
	"""
	if not os.path.isdir(source):
		raise NotADirectoryError(f"Source '{source}' is not a directory")

	# Collect all files to copy
	all_files: list[tuple[str, str]] = []
	for dirpath, _, filenames in os.walk(source):
		rel_dir = os.path.relpath(dirpath, source)
		dst_dir = os.path.join(destination, rel_dir) if rel_dir != "." else destination
		os.makedirs(dst_dir, exist_ok=True)
		for filename in filenames:
			src_file = os.path.join(dirpath, filename)
			dst_file = os.path.join(dst_dir, filename)
			all_files.append((src_file, dst_file))

	# Copy files with progress bar
	from ..print.progress_bar import colored_for_loop
	for src_file, dst_file in colored_for_loop(all_files, desc=desc):
		shutil.copy2(src_file, dst_file)

	return destination


def redirect_folder(
	source: str,
	destination: str,
	link_type: str | None = None,
) -> str:
	""" Move a folder from source to destination and create a link at the original source location.

	If the source is already a symlink or junction, the operation is skipped.
	If the destination path ends with ``/``, the source folder's basename is appended automatically.

	Link types:
		- ``"junction"`` (or ``"hardlink"``): Uses an NTFS junction on Windows,
			or a bind mount (``mount --bind``, requires sudo) on Linux.
			Falls back to symlink if junction/bind mount creation fails.
		- ``"symlink"``: Uses a symbolic link (may require elevated privileges on Windows).
		- ``None``: Prompts the user interactively.

	Args:
		source		(str):				Path to the existing folder to redirect
		destination	(str):				Path where the folder contents will be moved to
		link_type	(str | None):		``"hardlink"``/``"junction"``, ``"symlink"``, or None to ask
	Returns:
		str:	The final destination path

	Examples:

		.. code-block:: python

			> redirect_folder("C:/Games/MyGame", "D:/Games/")
			# Moves C:/Games/MyGame -> D:/Games/MyGame and creates a link at C:/Games/MyGame

			> redirect_folder("C:/Games/MyGame", "D:/Storage/MyGame")
			# Moves C:/Games/MyGame -> D:/Storage/MyGame and creates a link at C:/Games/MyGame
	"""
	from ..print.message import info, warning

	# Clean paths
	source = clean_path(source, trailing_slash=False)
	destination = clean_path(destination, trailing_slash=True)

	# If destination ends with "/", append source basename
	if destination.endswith("/"):
		destination = destination + os.path.basename(source)
	destination = clean_path(destination, trailing_slash=False)

	# Validate source
	if not os.path.exists(source):
		warning(f"Source directory '{source}' does not exist")
		choice = input(f"{Cfg.CYAN}Do you want to continue anyway? [y/N]: {Cfg.RESET}").strip().lower()
		if choice not in ("y", "yes"):
			info(f"{Cfg.RED}Aborted.{Cfg.RESET}")
			return ""
	elif not os.path.isdir(source):
		raise NotADirectoryError(f"Source '{source}' is not a directory")

	# Check if source is already a link (symlink or junction)
	if is_junction(source):
		warning(f"Source '{source}' is already a symlink or junction, skipping.")
		return destination

	# Check if destination already exists and is not empty
	if os.path.exists(destination):
		if os.path.isdir(destination) and os.listdir(destination):
			warning(f"Destination '{destination}' already exists and is not empty")
			choice = input(f"{Cfg.CYAN}Do you want to merge into the existing folder? [y/N]: {Cfg.RESET}").strip().lower()
			if choice not in ("y", "yes"):
				info(f"{Cfg.RED}Aborted.{Cfg.RESET}")
				return ""

	# Normalize link_type aliases
	if link_type is not None:
		link_type = link_type.lower().strip()
		if link_type in ("hardlink", "hard", "junction", "j"):
			link_type = "junction"
		elif link_type in ("symlink", "sym", "symbolic", "s"):
			link_type = "symlink"
		else:
			raise ValueError(f"Invalid link_type '{link_type}'. Use 'hardlink'/'junction' or 'symlink'.")

	# Ask user if link_type not specified
	if link_type is None:
		print(f"\n{Cfg.CYAN}How should '{source}' be linked to '{destination}'?{Cfg.RESET}")
		if os.name == "nt":
			print(f"  {Cfg.GREEN}1{Cfg.RESET}) Junction / Hardlink  (recommended on Windows, no admin required)")
		else:
			print(f"  {Cfg.GREEN}1{Cfg.RESET}) Bind mount           (not recommended on Linux, requires sudo)")
		print(f"  {Cfg.GREEN}2{Cfg.RESET}) Symlink              (works everywhere)")
		while True:
			choice = input(f"\n{Cfg.CYAN}Choose [1/2]: {Cfg.RESET}").strip()
			if choice == "1":
				link_type = "junction"
				break
			elif choice == "2":
				link_type = "symlink"
				break
			else:
				print("Please enter 1 or 2.")

	# Move source to destination
	dest_parent: str = os.path.dirname(destination)
	if dest_parent:
		os.makedirs(dest_parent, exist_ok=True)
	if os.path.exists(source):
		info(f"Copying '{source}' -> '{destination}'")
		copytree_with_progress(source, destination, desc=f"Copying '{os.path.basename(source)}'")
		info(f"Removing original '{source}'")
		shutil.rmtree(source)
	else:
		info(f"Source does not exist, creating destination '{destination}'")
		os.makedirs(destination, exist_ok=True)

	# Create link at source pointing to destination
	abs_destination = clean_path(os.path.abspath(destination), trailing_slash=False)
	if link_type == "junction":
		if os.name == "nt":
			# Use junction on Windows
			try:
				info(f"Creating junction '{source}' -> '{abs_destination}'")
				create_junction(source, abs_destination)
			except OSError:
				# Fallback to symlink if junction fails (e.g., different filesystem type)
				warning("Junction creation failed, falling back to symlink")
				info(f"Creating symlink '{source}' -> '{abs_destination}'")
				os.symlink(abs_destination, source, target_is_directory=True)
		else:
			# On Linux/macOS, use bind mount (equivalent of Windows junction)
			try:
				os.makedirs(source, exist_ok=True)
				info(f"Creating bind mount '{source}' -> '{abs_destination}'")
				create_bind_mount(source, abs_destination)
				warning(
					"Bind mounts do not persist across reboots. "
					"To make it permanent, add this line to /etc/fstab:\n"
					f"\t{abs_destination} {os.path.abspath(source)} none bind 0 0"
				)
			except OSError:
				# Fallback to symlink if bind mount fails (e.g., not root)
				warning("Bind mount failed (requires sudo), falling back to symlink")
				# Remove the empty directory created for the mount point
				if os.path.isdir(source) and not os.listdir(source):
					os.rmdir(source)
				info(f"Creating symlink '{source}' -> '{abs_destination}'")
				os.symlink(abs_destination, source, target_is_directory=True)
	else:
		# Symlink
		info(f"Creating symlink '{source}' -> '{abs_destination}'")
		os.symlink(abs_destination, source, target_is_directory=True)

	return destination


def redirect_cli() -> None:
	""" CLI entry point for the redirect command.
	Usage: stouputils redirect <source> <destination> [--hardlink|--symlink]
	"""
	import argparse
	parser = argparse.ArgumentParser(
		prog="stouputils redirect",
		description="Move a folder to a new location and create a junction/symlink at the original path.",
	)
	parser.add_argument("source", help="Source folder to redirect")
	parser.add_argument("destination", help="Destination path (append '/' to auto-use source basename)")
	group = parser.add_mutually_exclusive_group()
	group.add_argument("--hardlink", "--junction", action="store_const", const="junction", dest="link_type", help="Use a junction (Windows) or fallback to symlink (Linux/macOS)")
	group.add_argument("--symlink", action="store_const", const="symlink", dest="link_type", help="Use a symbolic link")
	args = parser.parse_args()
	redirect_folder(args.source, args.destination, link_type=args.link_type)

