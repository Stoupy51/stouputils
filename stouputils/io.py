"""
This module provides utilities for file management.

- replace_tilde: Replace the "~" by the user's home directory
- clean_path: Clean the path by replacing backslashes with forward slashes and simplifying the path
- super_open: Open a file with the given mode, creating the directory if it doesn't exist (only if writing)
- super_copy: Copy a file (or a folder) from the source to the destination (always create the directory)
- super_json_load: Load a JSON file from the given path
- super_json_dump: Writes the provided data to a JSON file with a specified indentation depth.

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/io_module.gif
  :alt: stouputils io examples
"""

# Imports
import shutil
import json
import os
import io
from typing import IO, Any

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
	return path.replace("~", os.path.expanduser("~")).replace("\\", "/")

# Utility function to clean the path
def clean_path(file_path: str) -> str:
	""" Clean the path by replacing backslashes with forward slashes and simplifying the path

	Args:
		file_path (str): The path to clean
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

	return file_path


# Function that takes a relative path and returns the absolute path of the directory
def get_root_path(relative_path: str, go_up: int = 0) -> str:
	""" Get the absolute path of the directory. Usually used to get the root path of the project using the __file__ variable.

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
	)


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
	if "/" in file_path and "w" in mode:
		os.makedirs(os.path.dirname(file_path), exist_ok=True)

	# Open file and return
	if "b" in mode:
		return open(file_path, mode)
	else:
		return open(file_path, mode, encoding = encoding) # Always use utf-8 encoding to avoid issues



# For easy file copy
def super_copy(src: str, dst: str, create_dir: bool = True) -> str:
	""" Copy a file (or a folder) from the source to the destination

	Args:
		src	(str): The source path
		dst	(str): The destination path
		create_dir (bool): Whether to create the directory if it doesn't exist (default: True)
	Returns:
		str: The destination path
	"""
	# Make directory
	if create_dir:
		os.makedirs(os.path.dirname(dst), exist_ok=True)

	# If source is a folder, copy it recursively
	if os.path.isdir(src):
		return shutil.copytree(src, dst, dirs_exist_ok = True)
	else:
		return shutil.copy(src, dst)



# JSON load from file path
def super_json_load(file_path: str) -> Any:
	""" Load a JSON file from the given path

	Args:
		file_path (str): The path to the JSON file
	Returns:
		Any: The content of the JSON file
	"""
	with super_open(file_path, "r") as f:
		return json.load(f)



# JSON dump with indentation for levels
def super_json_dump(data: Any, file: io.TextIOWrapper|None = None, max_level: int = 2, indent: str = '\t') -> str:
	""" Writes the provided data to a JSON file with a specified indentation depth.
	For instance, setting max_level to 2 will limit the indentation to 2 levels.

	Args:
		data (Any): 				The data to dump (usually a dict or a list)
		file (io.TextIOWrapper): 	The file to dump the data to, if None, the data is returned as a string
		max_level (int):			The depth of indentation to stop at (-1 for infinite)
		indent (str):				The indentation character (default: '\t')
	Returns:
		str: The content of the file in every case
	
	>>> super_json_dump({"a": [[1,2,3]], "b": 2}, max_level = 2)
	'{\\n\\t"a": [\\n\\t\\t[1,2,3]\\n\\t],\\n\\t"b": 2\\n}\\n'
	"""
	content: str = json.dumps(data, indent=indent, ensure_ascii = False)
	if max_level > -1:

		# Seek in content to remove to high indentations
		longest_indentation: int = 0
		for line in content.split("\n"):
			indentation: int = 0
			for char in line:
				if char == "\t":
					indentation += 1
				else:
					break
			longest_indentation = max(longest_indentation, indentation)
		for i in range(longest_indentation, max_level, -1):
			content = content.replace("\n" + indent * i, "")
			pass

		# To finalyze, fix the last indentations
		finishes: tuple[str, str] = ('}', ']')
		for char in finishes:
			to_replace: str = "\n" + indent * max_level + char
			content = content.replace(to_replace, char)
	
	# Write file content and return it
	content += "\n"
	if file:
		file.write(content)
	return content


