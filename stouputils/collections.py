"""
This module provides utilities for collection manipulation:

- unique_list: Remove duplicates from a list while preserving order using object id, hash or str

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/collections_module.gif
  :alt: stouputils collections examples
"""

# Imports
from typing import Any, Literal


# Functions
def unique_list(list_to_clean: list[Any], method: Literal["id", "hash", "str"] = "str") -> list[Any]:
	""" Remove duplicates from the list while keeping the order using ids (default) or hash or str

	Args:
		list_to_clean	(list[Any]):					The list to clean
		method			(Literal["id", "hash", "str"]):	The method to use to identify duplicates
	Returns:
		list[Any]: The cleaned list

	Examples:
		>>> unique_list([1, 2, 3, 2, 1], method="id")
		[1, 2, 3]

		>>> s1 = {1, 2, 3}
		>>> s2 = {2, 3, 4}
		>>> s3 = {1, 2, 3}
		>>> unique_list([s1, s2, s1, s1, s3, s2, s3], method="id")
		[{1, 2, 3}, {2, 3, 4}, {1, 2, 3}]

		>>> s1 = {1, 2, 3}
		>>> s2 = {2, 3, 4}
		>>> s3 = {1, 2, 3}
		>>> unique_list([s1, s2, s1, s1, s3, s2, s3], method="str")
		[{1, 2, 3}, {2, 3, 4}]
	"""
	# Initialize the seen ids set and the result list
	seen: set[Any] = set()
	result: list[Any] = []

	# Iterate over each item in the list
	for item in list_to_clean:
		if method == "id":
			item_identifier = id(item)
		elif method == "hash":
			item_identifier = hash(item)
		elif method == "str":
			item_identifier = str(item)
		else:
			raise ValueError(f"Invalid method: {method}")

		# If the item id is not in the seen ids set, add it to the seen ids set and append the item to the result list
		if item_identifier not in seen:
			seen.add(item_identifier)
			result.append(item)

	# Return the cleaned list
	return result

