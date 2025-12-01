"""
This module provides utilities for file management.

- get_root_path: Get the absolute path of the directory
- relative_path: Get the relative path of a file relative to a given directory
- super_json_dump: Writes the provided data to a JSON file with a specified indentation depth.
- super_json_load: Load a JSON file from the given path
- super_csv_dump: Writes data to a CSV file with customizable options
- super_csv_load: Load a CSV file from the given path
- super_copy: Copy a file (or a folder) from the source to the destination (always create the directory)
- super_open: Open a file with the given mode, creating the directory if it doesn't exist (only if writing)
- replace_tilde: Replace the "~" by the user's home directory
- clean_path: Clean the path by replacing backslashes with forward slashes and simplifying the path

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/io_module.gif
  :alt: stouputils io examples
"""

# Imports
import csv
import os
import re
import shutil
from io import StringIO
from typing import IO, Any

import orjson
import pyfastcopy  # type: ignore  # noqa: F401


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
def super_json_dump(data: Any, file: IO[Any]|None = None, max_level: int = 2, indent: str | int = '\t', suffix: str = "\n") -> str:
	r""" Writes the provided data to a JSON file with a specified indentation depth.
	For instance, setting max_level to 2 will limit the indentation to 2 levels.

	Args:
		data (Any): 				The data to dump (usually a dict or a list)
		file (IO[Any]): 			The file to dump the data to, if None, the data is returned as a string
		max_level (int):			The depth of indentation to stop at (-1 for infinite)
		indent (str | int):			The indentation character (default: '\t')
		suffix (str):				The suffix to add at the end of the string (default: '\n')
	Returns:
		str: The content of the file in every case

	>>> super_json_dump({"a": [[1,2,3]], "b": 2}, max_level = 0)
	'{"a": [[1,2,3]],"b": 2}\n'
	>>> super_json_dump({"a": [[1,2,3]], "b": 2}, max_level = 1)
	'{\n\t"a": [[1,2,3]],\n\t"b": 2\n}\n'
	>>> super_json_dump({"a": [[1,2,3]], "b": 2}, max_level = 2)
	'{\n\t"a": [\n\t\t[1,2,3]\n\t],\n\t"b": 2\n}\n'
	>>> super_json_dump({"a": [[1,2,3]], "b": 2}, max_level = 3)
	'{\n\t"a": [\n\t\t[\n\t\t\t1,\n\t\t\t2,\n\t\t\t3\n\t\t]\n\t],\n\t"b": 2\n}\n'
	"""
	# Normalize indentation to string
	if isinstance(indent, int):
		indent = ' ' * indent

	# Dump content with 2-space indent and replace it with the desired indent
	content: str = orjson.dumps(data, option=orjson.OPT_INDENT_2).decode("utf-8")
	if indent != "  ":
		content = re.sub(
			pattern=r'^(\s{2})+',  # Match groups of 2 spaces at start of lines
			repl=lambda match: indent * (len(match.group(0)) // 2),  # Convert to desired indent
			string=content,
			flags=re.MULTILINE
		)

	# Limit max depth of indentation
	if max_level > -1:
		escape: str = re.escape(indent)
		pattern: re.Pattern[str] = re.compile(
			r"\n" + escape + "{" + str(max_level + 1) + r",}(.*)"
			r"|\n" + escape + "{" + str(max_level) + r"}([}\]])"
		)
		content = pattern.sub(r"\1\2", content)

	# Final newline and write
	content += suffix
	if file:
		file.write(content)
	return content

# JSON load from file path
def super_json_load(file_path: str) -> Any:
	""" Load a JSON file from the given path

	Args:
		file_path (str): The path to the JSON file
	Returns:
		Any: The content of the JSON file
	"""
	with super_open(file_path, "r") as f:
		return orjson.loads(f.read())

# CSV dump to file
def super_csv_dump(data: Any, file: IO[Any] | None = None, delimiter: str = ',', has_header: bool = True, index: bool = False, *args: Any, **kwargs: Any) -> str:
	""" Writes data to a CSV file with customizable options

	Args:
		data (list[list[Any]] | list[dict[str, Any]] | pd.DataFrame | pl.DataFrame): The data to write, either a list of lists, list of dicts, pandas DataFrame, or Polars DataFrame
		file (IO[Any]): The file to dump the data to, if None, the data is returned as a string
		delimiter (str): The delimiter to use (default: ',')
		has_header (bool): Whether to include headers (default: True, applies to dict and DataFrame data)
		index (bool): Whether to include the index (default: False, only applies to pandas DataFrame)
		*args: Additional positional arguments to pass to the underlying CSV writer or DataFrame method
		**kwargs: Additional keyword arguments to pass to the underlying CSV writer or DataFrame method
	Returns:
		str: The CSV content as a string

	Examples:

		>>> super_csv_dump([["a", "b", "c"], [1, 2, 3], [4, 5, 6]])
		'a,b,c\\r\\n1,2,3\\r\\n4,5,6\\r\\n'

		>>> super_csv_dump([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])
		'name,age\\r\\nAlice,30\\r\\nBob,25\\r\\n'
	"""
	if isinstance(data, str | bytes | dict):
		raise ValueError("Data must be a list of lists, list of dicts, pandas DataFrame, or Polars DataFrame")
	output = StringIO()

	# Handle Polars DataFrame
	try:
		import polars as pl  # type: ignore  # noqa: F401
		copy_kwargs = kwargs.copy()
		copy_kwargs.setdefault("separator", delimiter)
		copy_kwargs.setdefault("include_header", has_header)
		copy_kwargs.setdefault("line_terminator", "\r\n")
		data.write_csv(output, *args, **copy_kwargs)
	except AttributeError:
		pass

	# Handle pandas DataFrame
	try:
		import pandas as pd  # type: ignore  # noqa: F401
		copy_kwargs = kwargs.copy()
		copy_kwargs.setdefault("index", index)
		copy_kwargs.setdefault("sep", delimiter)
		copy_kwargs.setdefault("header", has_header)
		copy_kwargs.setdefault("lineterminator", "\r\n")
		data.to_csv(output, *args, **copy_kwargs)
	except AttributeError:
		pass

	# Handle list of dicts
	if isinstance(data[0], dict):
		fieldnames = list(data[0].keys())
		kwargs.setdefault("fieldnames", fieldnames)
		kwargs.setdefault("delimiter", delimiter)
		kwargs.setdefault("lineterminator", "\r\n")
		dict_writer = csv.DictWriter(output, *args, **kwargs)
		if has_header:
			dict_writer.writeheader()
		dict_writer.writerows(data)  # type: ignore

	# Handle list of lists
	else:
		kwargs.setdefault("delimiter", delimiter)
		kwargs.setdefault("lineterminator", "\r\n")
		list_writer = csv.writer(output, *args, **kwargs)
		list_writer.writerows(data)

	content: str = output.getvalue()
	if file:
		file.write(content)
	output.close()
	return content

# CSV load from file path
def super_csv_load(file_path: str, delimiter: str = ',', has_header: bool = True, as_dict: bool = False, as_dataframe: bool = False, use_polars: bool = False, *args: Any, **kwargs: Any) -> Any:
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
			> super_csv_load("test.csv")
			[['1', '2', '3'], ['4', '5', '6']]

			> super_csv_load("test.csv", as_dict=True)
			[{'a': '1', 'b': '2', 'c': '3'}, {'a': '4', 'b': '5', 'c': '6'}]

			> super_csv_load("test.csv", as_dataframe=True)
			   a  b  c
			0  1  2  3
			1  4  5  6

			> super_csv_load("test.csv", as_dataframe=True, use_polars=True)
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
				return pl.DataFrame()
			kwargs.setdefault("separator", delimiter)
			kwargs.setdefault("has_header", has_header)
			return pl.read_csv(file_path, *args, **kwargs)
		else:
			import pandas as pd  # type: ignore
			if not os.path.exists(file_path):
				return pd.DataFrame()
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
		symlink     (bool): Whether to create a symlink instead of copying (Linux only, default: True)
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
	return path.replace("~", os.path.expanduser("~")).replace("\\", "/")

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

