
# Imports
import os
import shutil
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

