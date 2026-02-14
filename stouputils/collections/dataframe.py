
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
		df				(pl.DataFrame):		The Polars DataFrame to update.
		new_entry		(dict[str, Any]):	The new entry to insert or update.
		primary_keys	(list[str] | dict[str, Any] | None):	The primary keys to identify the row (for updates).
	Returns:
		pl.DataFrame: The updated Polars DataFrame.
	Examples:
		>>> import polars as pl
		>>> df = pl.DataFrame({"id": [1, 2], "value": ["a", "b"]})
		>>> new_entry = {"id": 2, "value": "updated"}
		>>> updated_df = upsert_in_dataframe(df, new_entry, primary_keys=["id"])
		>>> print(updated_df)
		shape: (2, 2)
		┌─────┬─────────┐
		│ id  ┆ value   │
		│ --- ┆ ---     │
		│ i64 ┆ str     │
		╞═════╪═════════╡
		│ 1   ┆ a       │
		│ 2   ┆ updated │
		└─────┴─────────┘

		>>> new_entry = {"id": 3, "value": "new"}
		>>> updated_df = upsert_in_dataframe(updated_df, new_entry, primary_keys=["id"])
		>>> print(updated_df)
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

	# Create new DataFrame if file doesn't exist or is invalid
	if df.is_empty():
		return pl.DataFrame([new_entry])

	# If no primary keys provided, return DataFrame with new entry appended
	if not primary_keys:
		new_row_df = pl.DataFrame([new_entry])
		return pl.concat([df, new_row_df], how="diagonal_relaxed")

	# If primary keys are provided as a list, convert to dict with values from new_entry
	if isinstance(primary_keys, list):
		primary_keys = {key: new_entry[key] for key in primary_keys if key in new_entry}

	# Build mask based on primary keys
	mask: pl.Expr = pl.lit(True)
	for key, value in primary_keys.items():
		if key in df.columns:
			mask = mask & (df[key] == value)
		else:
			# Primary key column doesn't exist, so no match possible
			mask = pl.lit(False)
			break

	# Insert or update row based on primary keys
	if df.select(mask).to_series().any():
		# Update existing row
		for key, value in new_entry.items():
			if key in df.columns:
				df = df.with_columns(pl.when(mask).then(pl.lit(value)).otherwise(pl.col(key)).alias(key))
			else:
				# Add new column if it doesn't exist
				df = df.with_columns(pl.when(mask).then(pl.lit(value)).otherwise(None).alias(key))
		return df
	else:
		# Insert new row
		new_row_df = pl.DataFrame([new_entry])
		return pl.concat([df, new_row_df], how="diagonal_relaxed")

