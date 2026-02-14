
# Imports
import csv
import os
from io import StringIO
from typing import IO, Any

from .path import super_open


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

