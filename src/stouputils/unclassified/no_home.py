
# Imports
from typing import Any

def unique_list(list_to_clean: list[Any]) -> list[Any]:
	""" Remove duplicates from the list while keeping the order using ids

	Args:
		list_to_clean (list[Any]): The list to clean
	Returns:
		list[Any]: The cleaned list
	"""
	# Initialize the seen ids set and the result list
	seen_ids: set[int] = set()
	result: list[Any] = []

	# Iterate over each item in the list
	for item in list_to_clean:
		item_id: int = id(item)

		# If the item id is not in the seen ids set, add it to the seen ids set and append the item to the result list
		if item_id not in seen_ids:
			seen_ids.add(item_id)
			result.append(item)

	# Return the cleaned list
	return result

