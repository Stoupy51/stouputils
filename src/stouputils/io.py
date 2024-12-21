"""
This module provides utilities for file management.
- replace_tilde: Replace the "~" by the user's home directory
- clean_path: Clean the path by replacing backslashes with forward slashes and simplifying the path
- super_open: Open a file with the given mode, creating the directory if it doesn't exist (only if writing)
- super_copy: Copy a file (or a folder) from the source to the destination (always create the directory)
- super_json_load: Load a JSON file from the given path
- super_json_dump: Writes the provided data to a JSON file with a specified indentation depth.
"""

# Imports
from .decorators import *
import shutil
import json
import os
import io
from typing import IO

# Function that replace the "~" by the user's home directory
def replace_tilde(path: str) -> str:
	return path.replace("~", os.path.expanduser("~"))

# Utility function to clean the path
def clean_path(file_path: str) -> str:
	""" Clean the path by replacing backslashes with forward slashes and simplifying the path

	Args:
		file_path (str): The path to clean
	Returns:
		str: The cleaned path
	
	>>> clean_path("C:\\\\Users\\\\Stoupy\\\\Documents\\\\test.txt")
	'C:/Users/Stoupy/Documents/test.txt'

	>>> clean_path("Some Folder////")
	'Some Folder/'

	>>> clean_path("test/uwu/1/../../")
	'test/'

	>>> clean_path("some/./folder/../")
	'some/'
	"""
	# Replace backslashes with forward slashes and double slashes
	while "//" in file_path or "\\" in file_path:
		file_path = file_path.replace("\\", "/").replace("//", "/")

	# Replace tilde
	file_path = replace_tilde(file_path)

	# If the path contains "../", simplify it
	if "../" in file_path:
		# Split the path into parts
		splitted: list[str] = file_path.split("/")
		new_splitted: list[str] = []

		# Iterate over each part of the path
		for part in splitted:
			if part == "..":
				if new_splitted and new_splitted[-1] != "..":
					new_splitted.pop()
			else:
				new_splitted.append(part)
		file_path = "/".join(new_splitted)

	# Replace backslashes with forward slashes and double slashes
	while "//" in file_path:
		file_path = file_path.replace("//", "/")

	# Replace "./" with nothing since it's useless
	file_path = file_path.replace("./", "")

	# Return the cleaned path
	return file_path



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


