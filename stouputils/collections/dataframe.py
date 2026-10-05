
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from typing import TYPE_CHECKING, Any

# Lazy imports for typing
if TYPE_CHECKING:
	import polars as pl

# Functions
def upsert_in_dataframe(
	df: "pl.DataFrame",
	new_entry: dict[str, Any],
	primary_keys: list[str] | dict[str, Any] | None = None
) -> "pl.DataFrame":
	""" Insert or update a row in the Polars DataFrame based on primary keys.

	Args:
		df:           The Polars DataFrame to update.
		new_entry:    The new entry to insert or update.
		primary_keys: The primary keys to identify the row (for updates).
	Returns:
		The updated Polars DataFrame.
	>>> import polars as pl  # doctest: +SKIP
	>>> df = pl.DataFrame({"id": [1, 2], "value": ["a", "b"]})  # doctest: +SKIP
	>>> new_entry = {"id": 2, "value": "updated"}  # doctest: +SKIP
	>>> updated_df = upsert_in_dataframe(df, new_entry, primary_keys=["id"])  # doctest: +SKIP
	>>> print(updated_df)  # doctest: +SKIP
	shape: (2, 2)
	┌─────┬─────────┐
	│ id  ┆ value   │
	│ --- ┆ ---     │
	│ i64 ┆ str     │
	╞═════╪═════════╡
	│ 1   ┆ a       │
	│ 2   ┆ updated │
	└─────┴─────────┘

	>>> new_entry = {"id": 3, "value": "new"}  # doctest: +SKIP
	>>> updated_df = upsert_in_dataframe(updated_df, new_entry, primary_keys=["id"])  # doctest: +SKIP
	>>> print(updated_df)  # doctest: +SKIP
	shape: (3, 2)
	┌─────┬─────────┐
	│ id  ┆ value   │
	│ --- ┆ ---     │
	│ i64 ┆ str     │
	╞═════╪═════════╡
	│ 1   ┆ a       │
	│ 2   ┆ updated │
	│ 3   ┆ new     │
	└─────┴─────────┘
	"""
	# Imports
	import polars as pl

	new_row_df: pl.DataFrame = pl.DataFrame([new_entry])
	if df.is_empty():
		return new_row_df
	if not primary_keys:
		return pl.concat([df, new_row_df], how="diagonal_relaxed")
	if isinstance(primary_keys, list):
		primary_keys = {key: new_entry[key] for key in primary_keys if key in new_entry}

	# A primary key column the frame lacks matches no row
	mask: pl.Expr = pl.lit(False) if any(key not in df.columns for key in primary_keys) else pl.all_horizontal(
		pl.lit(True), *(pl.col(key) == value for key, value in primary_keys.items())
	)
	if not df.select(mask).to_series().any():
		return pl.concat([df, new_row_df], how="diagonal_relaxed")
	return df.with_columns(
		pl.when(mask).then(pl.lit(value)).otherwise(pl.col(key) if key in df.columns else None).alias(key)
		for key, value in new_entry.items()
	)

