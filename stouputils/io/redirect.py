
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import os
import shutil

from ..config import StouputilsConfig as Cfg
from .path import clean_path

# Constants
LINK_TYPE_ALIASES: dict[str, str] = {
	"hardlink": "junction", "hard": "junction", "junction": "junction", "j": "junction",
	"symlink": "symlink", "sym": "symlink", "symbolic": "symlink", "s": "symlink",
}
""" Accepted spellings of a ``link_type``, by the kind of link each one makes. """


# Functions
def is_junction(path: str) -> bool:
	""" Check if a path is a junction point (Windows) or a symlink (any OS).

	Args:
		path: The path to check
	Returns:
		True if the path is a junction or symlink
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
		source: The junction path to create (with forward slashes, will be converted)
		target: The target directory the junction points to
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
		source: The mount point path to create (must exist as an empty directory)
		target: The target directory to bind
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

	Uses :func:`~stouputils.print.progress_bar.progress_bar` to display progress while copying each file.
	Directory structure is created automatically. Existing files at the destination are overwritten.

	Args:
		source:      Path to the source directory to copy
		destination: Path to the destination directory
		desc:        Description for the progress bar (default: ``"Copying"``)
	Returns:
		The destination path
	Raises:
		:py:exc:`NotADirectoryError`: If source is not a directory

	.. code-block:: python

		import stouputils as stp

		# Create a folder with 3000 small files
		for index in range(3000):
			stp.super_open(f"photos/2026/photo_{index}.txt", "w").write("pixels")

		# Copy it with a progress bar, creating the destination folders on the way
		stp.copytree_with_progress("photos", "backup/photos")

	.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/copytree_with_progress.svg
		:alt: Terminal output of the example, a progress bar filling up
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
	from ..print.progress_tqdm import progress_bar
	for src_file, dst_file in progress_bar(all_files, desc=desc):
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
		source:      Path to the existing folder to redirect
		destination: Path where the folder contents will be moved to
		link_type:   ``"hardlink"``/``"junction"``, ``"symlink"``, or None to ask
	Returns:
		The final destination path

	.. code-block:: python

		import os
		import stouputils as stp

		# A game folder on the main disk
		for index in range(500):
			stp.super_open(f"games/MyGame/level_{index}.bin", "w").write("level data")

		# Move it to another disk and leave a link at the old place, so nothing else has to change
		stp.redirect_folder("games/MyGame", "other_disk/games/", link_type="symlink")
		stp.info("games/MyGame now points to", os.readlink("games/MyGame"))

	.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/redirect_folder.svg
		:alt: Terminal output of the example, the folder copied then replaced by a link
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
		if not confirm_or_abort("Do you want to continue anyway?"):
			return ""
	elif not os.path.isdir(source):
		raise NotADirectoryError(f"Source '{source}' is not a directory")

	# Check if source is already a link (symlink or junction)
	if is_junction(source):
		warning(f"Source '{source}' is already a symlink or junction, skipping.")
		return destination

	# Check if destination already exists and is not empty
	if os.path.isdir(destination) and os.listdir(destination):
		warning(f"Destination '{destination}' already exists and is not empty")
		if not confirm_or_abort("Do you want to merge into the existing folder?"):
			return ""

	# Normalize link_type aliases, or ask the user when not specified
	link_type = ask_link_type(source, destination) if link_type is None else normalize_link_type(link_type)

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

	create_link(source, clean_path(os.path.abspath(destination), trailing_slash=False), link_type)
	return destination


def confirm_or_abort(question: str) -> bool:
	""" Ask a yes/no question on stdin, no being the default, and report the abort when the answer is no. """
	from ..print.message import info
	if input(f"{Cfg.CYAN}{question} [y/N]: {Cfg.RESET}").strip().lower() in ("y", "yes"):
		return True
	info(f"{Cfg.RED}Aborted.{Cfg.RESET}")
	return False


def normalize_link_type(link_type: str) -> str:
	""" The kind of link an accepted spelling of ``link_type`` makes, ``"junction"`` or ``"symlink"``.

	Raises:
		ValueError: If the spelling is not one of ``LINK_TYPE_ALIASES``.

	>>> normalize_link_type(" Hard ")
	'junction'
	"""
	key: str = link_type.lower().strip()
	if key not in LINK_TYPE_ALIASES:
		raise ValueError(f"Invalid link_type '{key}'. Use 'hardlink'/'junction' or 'symlink'.")
	return LINK_TYPE_ALIASES[key]


def ask_link_type(source: str, destination: str) -> str:
	""" Ask on stdin how ``source`` should be linked to ``destination``.

	Returns:
		``"junction"`` or ``"symlink"``.
	"""
	print(f"\n{Cfg.CYAN}How should '{source}' be linked to '{destination}'?{Cfg.RESET}")
	if os.name == "nt":
		print(f"  {Cfg.GREEN}1{Cfg.RESET}) Junction / Hardlink  (recommended on Windows, no admin required)")
	else:
		print(f"  {Cfg.GREEN}1{Cfg.RESET}) Bind mount           (not recommended on Linux, requires sudo)")
	print(f"  {Cfg.GREEN}2{Cfg.RESET}) Symlink              (works everywhere)")
	while (choice := input(f"\n{Cfg.CYAN}Choose [1/2]: {Cfg.RESET}").strip()) not in ("1", "2"):
		print("Please enter 1 or 2.")
	return "junction" if choice == "1" else "symlink"


def create_link(source: str, target: str, link_type: str) -> None:
	""" Create a link at ``source`` pointing to the absolute ``target``.

	A ``"junction"`` is an NTFS junction on Windows and a bind mount elsewhere, and either falls back to a symlink when it fails.
	"""
	from ..print.message import info, warning
	if link_type == "junction":
		try:
			if os.name == "nt":
				info(f"Creating junction '{source}' -> '{target}'")
				create_junction(source, target)
			else:
				os.makedirs(source, exist_ok=True)
				info(f"Creating bind mount '{source}' -> '{target}'")
				create_bind_mount(source, target)
				warning(
					"Bind mounts do not persist across reboots. "
					"To make it permanent, add this line to /etc/fstab:\n"
					f"\t{target} {os.path.abspath(source)} none bind 0 0"
				)
			return
		except OSError:
			# A different filesystem type or a missing sudo, whose empty mount point would block the symlink
			warning(f"{'Junction creation' if os.name == 'nt' else 'Bind mount (requires sudo)'} failed, falling back to symlink")
			if os.path.isdir(source) and not os.listdir(source):
				os.rmdir(source)
	info(f"Creating symlink '{source}' -> '{target}'")
	os.symlink(target, source, target_is_directory=True)


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
	group.add_argument(
		"--hardlink", "--junction", action="store_const", const="junction", dest="link_type",
		help="Use a junction (Windows) or fallback to symlink (Linux/macOS)",
	)
	group.add_argument("--symlink", action="store_const", const="symlink", dest="link_type", help="Use a symbolic link")
	args = parser.parse_args()
	redirect_folder(args.source, args.destination, link_type=args.link_type)

