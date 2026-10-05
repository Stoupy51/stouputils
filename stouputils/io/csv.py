
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import csv
import os
from contextlib import suppress
from io import StringIO
from typing import IO, TYPE_CHECKING, Any, Literal, cast, overload

from ..typing import JsonDict, JsonList
from .path import super_open

if TYPE_CHECKING:
	import pandas as pd  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
	import polars as pl  # pyright: ignore[reportMissingImports]


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
		data:       The data to write, either a list of lists, list of dicts, pandas DataFrame, or Polars DataFrame
		file:       The file object or path to dump the data to
		delimiter:  The delimiter to use (default: ',')
		has_header: Whether to include headers (default: True, applies to dict and DataFrame data)
		index:      Whether to include the index (default: False, only applies to pandas DataFrame)
		*args:      Additional positional arguments to pass to the underlying CSV writer or DataFrame method
		**kwargs:   Additional keyword arguments to pass to the underlying CSV writer or DataFrame method
	Returns:
		The CSV content as a string

	>>> csv_dump([["a", "b", "c"], [1, 2, 3], [4, 5, 6]])
	'a,b,c\\r\\n1,2,3\\r\\n4,5,6\\r\\n'

	>>> csv_dump([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])
	'name,age\\r\\nAlice,30\\r\\nBob,25\\r\\n'
	"""
	if isinstance(data, str | bytes | dict):
		raise ValueError("Data must be a list of lists, list of dicts, pandas DataFrame, or Polars DataFrame")
	content: str = csv_text(data, delimiter, has_header, index, args, kwargs)
	if file:
		if isinstance(file, str):
			with super_open(file, "w") as f:
				f.write(content)
		else:
			file.write(content)
	return content


def csv_text(data: Any, delimiter: str, has_header: bool, index: bool, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
	""" The CSV text of a Polars or pandas DataFrame, or of a list of dicts or of lists, as :func:`csv_dump` writes it.

	Args:
		args:   Positional arguments for the underlying writer.
		kwargs: Keyword arguments for the underlying writer, overriding the ones built from the other parameters.
	"""
	output = StringIO()
	with suppress(ImportError):
		import polars as pl  # pyright: ignore[reportMissingImports]
		if isinstance(data, pl.DataFrame):
			data.write_csv(output, *args, **{"separator": delimiter, "include_header": has_header, **kwargs})
			return output.getvalue()
	with suppress(ImportError):
		import pandas as pd  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
		if isinstance(data, pd.DataFrame):
			cast(Any, data).to_csv(output, *args, **{"index": index, "sep": delimiter, "header": has_header, **kwargs})
			return output.getvalue()

	rows: JsonList = list(data)
	if isinstance(rows[0], dict):
		fieldnames: list[str] = list(cast(JsonDict, rows[0]).keys())
		dict_writer = csv.DictWriter(output, *args, **{"fieldnames": fieldnames, "delimiter": delimiter, **kwargs})
		if has_header:
			dict_writer.writeheader()
		dict_writer.writerows(rows)
	else:
		csv.writer(output, *args, **{"delimiter": delimiter, **kwargs}).writerows(rows)
	return output.getvalue()

# CSV load from file path
@overload
def csv_load(
	file_path: str,
	delimiter: str = ',',
	has_header: bool = True,
	as_dict: bool = False,
	*,
	as_dataframe: Literal[True],
	use_polars: Literal[True],
	**kwargs: Any
) -> "pl.DataFrame": ...

@overload
def csv_load(
	file_path: str,
	delimiter: str = ',',
	has_header: bool = True,
	as_dict: bool = False,
	*,
	as_dataframe: Literal[True],
	use_polars: Literal[False] = False,
	**kwargs: Any
) -> "pd.DataFrame": ...

@overload
def csv_load(
	file_path: str,
	delimiter: str = ',',
	has_header: bool = True,
	*,
	as_dict: Literal[True],
	as_dataframe: bool = False,
	use_polars: bool = False,
	**kwargs: Any
) -> list[dict[str, str]]: ...

@overload
def csv_load(
	file_path: str,
	delimiter: str = ',',
	has_header: bool = True,
	as_dict: bool = False,
	as_dataframe: bool = False,
	use_polars: bool = False,
	*args: Any,
	**kwargs: Any
) -> list[list[str]]: ...

def csv_load(
	file_path: str, delimiter: str = ',', has_header: bool = True, as_dict: bool = False, as_dataframe: bool = False,
	use_polars: bool = False, *args: Any, **kwargs: Any,
) -> Any:
	""" Load a CSV file from the given path

	Args:
		file_path:    The path to the CSV file
		delimiter:    The delimiter used in the CSV (default: ',')
		has_header:   Whether the CSV has a header row (default: True)
		as_dict:      Whether to return data as list of dicts (default: False)
		as_dataframe: Whether to return data as a DataFrame (default: False)
		use_polars:   Whether to use Polars instead of pandas for DataFrame (default: False, requires polars)
		*args:        Additional positional arguments to pass to the underlying CSV reader or DataFrame method
		**kwargs:     Additional keyword arguments to pass to the underlying CSV reader or DataFrame method
	Returns:
		The content of the CSV file

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
			import polars as pl  # pyright: ignore[reportMissingImports]
			if not os.path.exists(file_path):
				return pl.DataFrame() # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
			kwargs.setdefault("separator", delimiter)
			kwargs.setdefault("has_header", has_header)
			return pl.read_csv(file_path, *args, **kwargs) # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
		import pandas as pd  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
		if not os.path.exists(file_path):
			return pd.DataFrame() # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
		kwargs.setdefault("sep", delimiter)
		kwargs.setdefault("header", 0 if has_header else None)
		return pd.read_csv(file_path, *args, **kwargs) # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

	# Handle dict or list
	if not os.path.exists(file_path):
		return []
	with super_open(file_path, "r") as f:
		if as_dict or has_header:
			kwargs.setdefault("delimiter", delimiter)
			reader = csv.DictReader(f, *args, **kwargs)
			return list(reader)
		kwargs.setdefault("delimiter", delimiter)
		reader = csv.reader(f, *args, **kwargs)
		return list(reader)

