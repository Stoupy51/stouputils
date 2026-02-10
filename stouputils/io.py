"""
This module provides utilities for file management.

- get_root_path: Get the absolute path of the directory
- relative_path: Get the relative path of a file relative to a given directory
- json_dump: Writes the provided data to a JSON file with a specified indentation depth.
- json_load: Load a JSON file from the given path
- csv_dump: Writes data to a CSV file with customizable options
- csv_load: Load a CSV file from the given path
- super_copy: Copy a file (or a folder) from the source to the destination (always create the directory)
- super_open: Open a file with the given mode, creating the directory if it doesn't exist (only if writing)
- replace_tilde: Replace the "~" by the user's home directory
- clean_path: Clean the path by replacing backslashes with forward slashes and simplifying the path
- redirect_folder: Move a folder and create a junction/symlink at the original location
- safe_close: Safely close a file descriptor or file object after flushing, ignoring any exceptions

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/io_module.gif
  :alt: stouputils io examples
"""

# Imports
import csv
import json
import os
import re
import shutil
from io import StringIO
from typing import IO, Any


# Function that takes a relative path and returns the absolute path of the directory
def get_root_path(relative_path: str, go_up: int = 0) -> str:
	""" Get the absolute path of the directory.
	Usually used to get the root path of the project using the __file__ variable.

	Args:
		relative_path   (str): The path to get the absolute directory path from
		go_up           (int): Number of parent directories to go up (default: 0)
	Returns:
		str: The absolute path of the directory

	Examples:

		.. code-block:: python

			> get_root_path(__file__)
			'C:/Users/Alexandre-PC/AppData/Local/Programs/Python/Python310/lib/site-packages/stouputils'

			> get_root_path(__file__, 3)
			'C:/Users/Alexandre-PC/AppData/Local/Programs/Python/Python310'
	"""
	return clean_path(
		os.path.dirname(os.path.abspath(relative_path))
		+ "/.." * go_up
	) or "."

# Function that returns the relative path of a file
def relative_path(file_path: str, relative_to: str = "") -> str:
	""" Get the relative path of a file relative to a given directory.

	Args:
		file_path     (str): The path to get the relative path from
		relative_to   (str): The path to get the relative path to (default: current working directory -> os.getcwd())
	Returns:
		str: The relative path of the file
	Examples:

		>>> relative_path("D:/some/random/path/stouputils/io.py", "D:\\\\some")
		'random/path/stouputils/io.py'
		>>> relative_path("D:/some/random/path/stouputils/io.py", "D:\\\\some\\\\")
		'random/path/stouputils/io.py'
	"""
	if not relative_to:
		relative_to = os.getcwd()
	file_path = clean_path(file_path)
	relative_to = clean_path(relative_to)
	if file_path.startswith(relative_to):
		return clean_path(os.path.relpath(file_path, relative_to)) or "."
	else:
		return file_path or "."

# JSON dump with indentation for levels
def json_dump(
	data: Any,
	file: IO[Any] | str | None = None,
	max_level: int | None = 2,
	indent: str | int = '\t',
	suffix: str = "\n",
	ensure_ascii: bool = False
) -> str:
	r""" Writes the provided data to a JSON file with a specified indentation depth.
	For instance, setting max_level to 2 will limit the indentation to 2 levels.

	Args:
		data		(Any): 				The data to dump (usually a dict or a list)
		file		(IO[Any] | str): 	The file object or path to dump the data to
		max_level	(int | None):		The depth of indentation to stop at (-1 for infinite), None will default to 2
		indent		(str | int):		The indentation character (default: '\t')
		suffix		(str):				The suffix to add at the end of the string (default: '\n')
		ensure_ascii (bool):			Whether to escape non-ASCII characters (default: False)
	Returns:
		str: The content of the file in every case

	>>> json_dump({"a": [[1,2,3]], "b": 2}, max_level = 0)
	'{"a": [[1,2,3]],"b": 2}\n'
	>>> json_dump({"a": [[1,2,3]], "b": 2}, max_level = 1)
	'{\n\t"a": [[1,2,3]],\n\t"b": 2\n}\n'
	>>> json_dump({"a": [[1,2,3]], "b": 2}, max_level = 2)
	'{\n\t"a": [\n\t\t[1,2,3]\n\t],\n\t"b": 2\n}\n'
	>>> json_dump({"a": [[1,2,3]], "b": 2}, max_level = 3)
	'{\n\t"a": [\n\t\t[\n\t\t\t1,\n\t\t\t2,\n\t\t\t3\n\t\t]\n\t],\n\t"b": 2\n}\n'
	>>> json_dump({"éà": "üñ"}, ensure_ascii = True, max_level = 0)
	'{"\\u00e9\\u00e0": "\\u00fc\\u00f1"}\n'
	>>> json_dump({"éà": "üñ"}, ensure_ascii = False, max_level = 0)
	'{"éà": "üñ"}\n'
	"""
	# Handle None values for max_level
	if max_level is None:
		max_level = 2

	# Dump content with 2-space indent and replace it with the desired indent
	content: str = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)

	# Limit max depth of indentation
	if max_level > -1:
		escape: str = re.escape(indent if isinstance(indent, str) else ' '*indent)
		pattern: re.Pattern[str] = re.compile(
			r"\n" + escape + "{" + str(max_level + 1) + r",}(.*)"
			r"|\n" + escape + "{" + str(max_level) + r"}([}\]])"
		)
		content = pattern.sub(r"\1\2", content)

	# Final newline and write
	content += suffix
	if file:
		if isinstance(file, str):
			with super_open(file, "w") as f:
				f.write(content)
		else:
			file.write(content)
	return content

# JSON load from file path
def json_load(file_path: str) -> Any:
	""" Load a JSON file from the given path

	Args:
		file_path (str): The path to the JSON file
	Returns:
		Any: The content of the JSON file
	"""
	with open(file_path) as f:
		return json.loads(f.read())

# CSV dump to file
def csv_dump(
	data: Any,
	file: IO[Any] | str | None = None,
	delimiter: str = ',',
	has_header: bool = True,
	index: bool = False,
	*args: Any,
	**kwargs: Any
) -> str:
	""" Writes data to a CSV file with customizable options and returns the CSV content as a string.

	Args:
		data		(list[list[Any]] | list[dict[str, Any]] | pd.DataFrame | pl.DataFrame):
						The data to write, either a list of lists, list of dicts, pandas DataFrame, or Polars DataFrame
		file		(IO[Any] | str): The file object or path to dump the data to
		delimiter	(str): The delimiter to use (default: ',')
		has_header	(bool): Whether to include headers (default: True, applies to dict and DataFrame data)
		index		(bool): Whether to include the index (default: False, only applies to pandas DataFrame)
		*args		(Any): Additional positional arguments to pass to the underlying CSV writer or DataFrame method
		**kwargs	(Any): Additional keyword arguments to pass to the underlying CSV writer or DataFrame method
	Returns:
		str: The CSV content as a string

	Examples:

		>>> csv_dump([["a", "b", "c"], [1, 2, 3], [4, 5, 6]])
		'a,b,c\\r\\n1,2,3\\r\\n4,5,6\\r\\n'

		>>> csv_dump([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])
		'name,age\\r\\nAlice,30\\r\\nBob,25\\r\\n'
	"""
	if isinstance(data, str | bytes | dict):
		raise ValueError("Data must be a list of lists, list of dicts, pandas DataFrame, or Polars DataFrame")
	output = StringIO()
	done: bool = False

	# Handle Polars DataFrame
	import sys
	if sys.version_info >= (3, 14) and not sys._is_gil_enabled(): # pyright: ignore[reportPrivateUsage]
		# Skip Polars on free-threaded Python 3.14 due to segfault
		# TODO: Remove this check when Polars is fixed
		# See https://github.com/pola-rs/polars/issues/21889 and https://github.com/durandtibo/coola/issues/1066
		pass
	else:
		try:
			import polars as pl  # type: ignore
			if isinstance(data, pl.DataFrame):
				copy_kwargs = kwargs.copy()
				copy_kwargs.setdefault("separator", delimiter)
				copy_kwargs.setdefault("include_header", has_header)
				data.write_csv(output, *args, **copy_kwargs)
				done = True
		except Exception:
			pass

	# Handle pandas DataFrame
	if not done:
		try:
			import pandas as pd  # type: ignore
			if isinstance(data, pd.DataFrame):
				copy_kwargs = kwargs.copy()
				copy_kwargs.setdefault("index", index)
				copy_kwargs.setdefault("sep", delimiter)
				copy_kwargs.setdefault("header", has_header)
				data.to_csv(output, *args, **copy_kwargs)
		except Exception:
			pass

	if not done:
		# Handle list of dicts
		data = list(data)	# Ensure list and not other iterable
		if isinstance(data[0], dict):
			fieldnames = list(data[0].keys()) # type: ignore
			kwargs.setdefault("fieldnames", fieldnames)
			kwargs.setdefault("delimiter", delimiter)
			dict_writer = csv.DictWriter(output, *args, **kwargs)
			if has_header:
				dict_writer.writeheader()
			dict_writer.writerows(data)  # type: ignore
			done = True

		# Handle list of lists
		else:
			kwargs.setdefault("delimiter", delimiter)
			list_writer = csv.writer(output, *args, **kwargs)
			list_writer.writerows(data) # type: ignore
			done = True

	# If still not done, raise error
	if not done:
		output.close()
		raise ValueError(f"Data must be a list of lists, list of dicts, pandas DataFrame, or Polars DataFrame, got {type(data)} instead")

	# Get content and write to file if needed
	content: str = output.getvalue()
	if file:
		if isinstance(file, str):
			with super_open(file, "w") as f:
				f.write(content)
		else:
			file.write(content)
	output.close()
	return content

# CSV load from file path
def csv_load(file_path: str, delimiter: str = ',', has_header: bool = True, as_dict: bool = False, as_dataframe: bool = False, use_polars: bool = False, *args: Any, **kwargs: Any) -> Any:
	""" Load a CSV file from the given path

	Args:
		file_path (str): The path to the CSV file
		delimiter (str): The delimiter used in the CSV (default: ',')
		has_header (bool): Whether the CSV has a header row (default: True)
		as_dict (bool): Whether to return data as list of dicts (default: False)
		as_dataframe (bool): Whether to return data as a DataFrame (default: False)
		use_polars (bool): Whether to use Polars instead of pandas for DataFrame (default: False, requires polars)
		*args: Additional positional arguments to pass to the underlying CSV reader or DataFrame method
		**kwargs: Additional keyword arguments to pass to the underlying CSV reader or DataFrame method
	Returns:
		list[list[str]] | list[dict[str, str]] | pd.DataFrame | pl.DataFrame: The content of the CSV file

	Examples:

		.. code-block:: python

			> Assuming "test.csv" contains: a,b,c\\n1,2,3\\n4,5,6
			> csv_load("test.csv")
			[['1', '2', '3'], ['4', '5', '6']]

			> csv_load("test.csv", as_dict=True)
			[{'a': '1', 'b': '2', 'c': '3'}, {'a': '4', 'b': '5', 'c': '6'}]

			> csv_load("test.csv", as_dataframe=True)
			   a  b  c
			0  1  2  3
			1  4  5  6

		.. code-block:: console

			> csv_load("test.csv", as_dataframe=True, use_polars=True)
			shape: (2, 3)
			┌─────┬─────┬─────┐
			│ a   ┆ b   ┆ c   │
			│ --- ┆ --- ┆ --- │
			│ i64 ┆ i64 ┆ i64 │
			╞═════╪═════╪═════╡
			│ 1   ┆ 2   ┆ 3   │
			│ 4   ┆ 5   ┆ 6   │
			└─────┴─────┴─────┘
	"""  # noqa: E101
	# Handle DataFrame loading
	if as_dataframe:
		if use_polars:
			import polars as pl  # type: ignore
			if not os.path.exists(file_path):
				return pl.DataFrame() # type: ignore
			kwargs.setdefault("separator", delimiter)
			kwargs.setdefault("has_header", has_header)
			return pl.read_csv(file_path, *args, **kwargs) # type: ignore
		else:
			import pandas as pd  # type: ignore
			if not os.path.exists(file_path):
				return pd.DataFrame() # type: ignore
			kwargs.setdefault("sep", delimiter)
			kwargs.setdefault("header", 0 if has_header else None)
			return pd.read_csv(file_path, *args, **kwargs) # type: ignore

	# Handle dict or list
	if not os.path.exists(file_path):
		return []
	with super_open(file_path, "r") as f:
		if as_dict or has_header:
			kwargs.setdefault("delimiter", delimiter)
			reader = csv.DictReader(f, *args, **kwargs)
			return list(reader)
		else:
			kwargs.setdefault("delimiter", delimiter)
			reader = csv.reader(f, *args, **kwargs)
			return list(reader)

# For easy file copy
def super_copy(src: str, dst: str, create_dir: bool = True, symlink: bool = False) -> str:
	""" Copy a file (or a folder) from the source to the destination

	Args:
		src         (str):  The source path
		dst         (str):  The destination path
		create_dir  (bool): Whether to create the directory if it doesn't exist (default: True)
		symlink     (bool): Whether to create a symlink instead of copying (Linux only)
	Returns:
		str: The destination path
	"""
	# Disable symlink functionality on Windows as it uses shortcuts instead of proper symlinks
	if os.name == "nt":
		symlink = False

	# Create destination directory if needed
	if create_dir:
		os.makedirs(os.path.dirname(dst), exist_ok=True)

	# Handle directory copying
	if os.path.isdir(src):
		if symlink:

			# Remove existing destination if it's different from source
			if os.path.exists(dst):
				if os.path.samefile(src, dst) is False:
					if os.path.isdir(dst):
						shutil.rmtree(dst)
					else:
						os.remove(dst)
					return os.symlink(src.rstrip('/'), dst.rstrip('/'), target_is_directory=True) or dst
			else:
				return os.symlink(src.rstrip('/'), dst.rstrip('/'), target_is_directory=True) or dst

		# Regular directory copy
		else:
			return shutil.copytree(src, dst, dirs_exist_ok = True)

	# Handle file copying
	else:
		if symlink:

			# Remove existing destination if it's different from source
			if os.path.exists(dst):
				if os.path.samefile(src, dst) is False:
					os.remove(dst)
					return os.symlink(src, dst, target_is_directory=False) or dst
			else:
				return os.symlink(src, dst, target_is_directory=False) or dst

		# Regular file copy
		else:
			return shutil.copy(src, dst)
	return ""

# For easy file management
def super_open(file_path: str, mode: str, encoding: str = "utf-8") -> IO[Any]:
	""" Open a file with the given mode, creating the directory if it doesn't exist (only if writing)

	Args:
		file_path	(str): The path to the file
		mode		(str): The mode to open the file with, ex: "w", "r", "a", "wb", "rb", "ab"
		encoding	(str): The encoding to use when opening the file (default: "utf-8")
	Returns:
		open: The file object, ready to be used
	"""
	# Make directory
	file_path = clean_path(file_path)
	if "/" in file_path and ("w" in mode or "a" in mode):
		os.makedirs(os.path.dirname(file_path), exist_ok=True)

	# Open file and return
	if "b" in mode:
		return open(file_path, mode)
	else:
		return open(file_path, mode, encoding = encoding) # Always use utf-8 encoding to avoid issues

def read_file(file_path: str, encoding: str = "utf-8") -> str:
	""" Read the content of a file and return it as a string

	Args:
		file_path (str): The path to the file
		encoding  (str): The encoding to use when opening the file (default: "utf-8")
	Returns:
		str: The content of the file
	"""
	with super_open(file_path, "r", encoding=encoding) as f:
		return f.read()

# Function that replace the "~" by the user's home directory
def replace_tilde(path: str) -> str:
	""" Replace the "~" by the user's home directory

	Args:
		path (str): The path to replace the "~" by the user's home directory
	Returns:
		str: The path with the "~" replaced by the user's home directory
	Examples:

		.. code-block:: python

			> replace_tilde("~/Documents/test.txt")
			'/home/user/Documents/test.txt'
	"""
	# Only expand tilde if it's at the start of the path (not in middle like Windows short names)
	if path.startswith("~"):
		return os.path.expanduser(path).replace("\\", "/")
	return path.replace("\\", "/")

# Utility function to clean the path
def clean_path(file_path: str, trailing_slash: bool = True) -> str:
	""" Clean the path by replacing backslashes with forward slashes and simplifying the path

	Args:
		file_path (str): The path to clean
		trailing_slash (bool): Whether to keep the trailing slash, ex: "test/" -> "test/"
	Returns:
		str: The cleaned path
	Examples:
		>>> clean_path("C:\\\\Users\\\\Stoupy\\\\Documents\\\\test.txt")
		'C:/Users/Stoupy/Documents/test.txt'

		>>> clean_path("Some Folder////")
		'Some Folder/'

		>>> clean_path("test/uwu/1/../../")
		'test/'

		>>> clean_path("some/./folder/../")
		'some/'

		>>> clean_path("folder1/folder2/../../folder3")
		'folder3'

		>>> clean_path("./test/./folder/")
		'test/folder/'

		>>> clean_path("C:/folder1\\\\folder2")
		'C:/folder1/folder2'
	"""
	# Replace tilde
	file_path = replace_tilde(str(file_path))

	# Check if original path ends with slash
	ends_with_slash: bool = file_path.endswith('/') or file_path.endswith('\\')

	# Use os.path.normpath to clean up the path
	file_path = os.path.normpath(file_path)

	# Convert backslashes to forward slashes
	file_path = file_path.replace(os.sep, '/')

	# Add trailing slash back if original had one
	if ends_with_slash and not file_path.endswith('/'):
		file_path += '/'

	# Remove trailing slash if requested
	if not trailing_slash and file_path.endswith('/'):
		file_path = file_path[:-1]

	# Return the cleaned path
	return file_path if file_path != "." else ""

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
		OSError: If the bind mount command fails
	"""
	import subprocess
	result = subprocess.run(
		["sudo", "mount", "--bind", target, source],
		capture_output=True, text=True
	)
	if result.returncode != 0:
		raise OSError(f"Failed to create bind mount: {result.stderr.strip()}")

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
	# Clean paths
	source = clean_path(source, trailing_slash=False)
	destination = clean_path(destination, trailing_slash=True)

	# If destination ends with "/", append source basename
	if destination.endswith("/"):
		destination = destination + os.path.basename(source)
	destination = clean_path(destination, trailing_slash=False)

	# Validate source
	if not os.path.exists(source):
		from .print import CYAN, RED, RESET, warning
		warning(f"Source directory '{source}' does not exist")
		choice = input(f"{CYAN}Do you want to continue anyway? [y/N]: {RESET}").strip().lower()
		if choice not in ("y", "yes"):
			print(f"{RED}Aborted.{RESET}")
			return ""
	elif not os.path.isdir(source):
		raise NotADirectoryError(f"Source '{source}' is not a directory")

	# Check if source is already a link (symlink or junction)
	if is_junction(source):
		from .print import warning
		warning(f"Source '{source}' is already a symlink or junction, skipping.")
		return destination

	# Check if destination already exists and is not empty
	if os.path.exists(destination):
		if os.path.isdir(destination) and os.listdir(destination):
			raise FileExistsError(f"Destination '{destination}' already exists and is not empty")

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
		from .print import CYAN, GREEN, RESET
		print(f"\n{CYAN}How should '{source}' be linked to '{destination}'?{RESET}")
		if os.name == "nt":
			print(f"  {GREEN}1{RESET}) Junction / Hardlink  (recommended on Windows, no admin required)")
		else:
			print(f"  {GREEN}1{RESET}) Bind mount           (not recommended on Linux, requires sudo)")
		print(f"  {GREEN}2{RESET}) Symlink              (works everywhere)")
		while True:
			choice = input(f"\n{CYAN}Choose [1/2]: {RESET}").strip()
			if choice == "1":
				link_type = "junction"
				break
			elif choice == "2":
				link_type = "symlink"
				break
			else:
				print("Please enter 1 or 2.")

	# Move source to destination
	from .print import info
	dest_parent: str = os.path.dirname(destination)
	if dest_parent:
		os.makedirs(dest_parent, exist_ok=True)
	if os.path.exists(source):
		info(f"Copying '{source}' -> '{destination}'")
		shutil.copytree(source, destination, dirs_exist_ok=True)
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
				from .print import warning
				warning("Junction creation failed, falling back to symlink")
				info(f"Creating symlink '{source}' -> '{abs_destination}'")
				os.symlink(abs_destination, source, target_is_directory=True)
		else:
			# On Linux/macOS, use bind mount (equivalent of Windows junction)
			try:
				os.makedirs(source, exist_ok=True)
				info(f"Creating bind mount '{source}' -> '{abs_destination}'")
				create_bind_mount(source, abs_destination)
				from .print import warning
				warning(
					"Bind mounts do not persist across reboots. "
					"To make it permanent, add this line to /etc/fstab:\n"
					f"\t{abs_destination} {os.path.abspath(source)} none bind 0 0"
				)
			except OSError:
				# Fallback to symlink if bind mount fails (e.g., not root)
				from .print import warning
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


def safe_close(file: IO[Any] | int | Any | None) -> None:
	""" Safely close a file object (or file descriptor) after flushing, ignoring any exceptions.

	Args:
		file (IO[Any] | int | None): The file object or file descriptor to close
	"""
	if isinstance(file, int):
		if file != -1:
			for func in (os.fsync, os.close):
				try:
					func(file)
				except Exception:
					pass
	elif file:
		for func in ("flush", "close"):
			try:
				getattr(file, func)()
			except Exception:
				pass


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

