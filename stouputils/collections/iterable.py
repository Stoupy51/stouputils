
# Imports
from collections.abc import Callable, Iterable
from typing import Literal


# Functions
def unique_list[T](list_to_clean: Iterable[T], method: Literal["id", "hash", "str"] = "str") -> list[T]:
	""" Remove duplicates from the list while keeping the order using ids, hash, or str

	Args:
		list_to_clean	(Iterable[T]):					The list to clean
		method			(Literal["id", "hash", "str"]):	The method to use to identify duplicates
	Returns:
		list[T]: The cleaned list

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
	seen: set[int | str] = set()
	result: list[T] = []

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

def at_least_n[T](iterable: Iterable[T], predicate: Callable[[T], bool], n: int) -> bool:
	""" Return True if at least n elements in iterable satisfy predicate.
	It's like the built-in any() but for at least n matches.

	Stops iterating as soon as n matches are found (short-circuit evaluation).

	Args:
		iterable	(Iterable[T]):			The iterable to check.
		predicate	(Callable[[T], bool]):	The predicate to apply to items.
		n			(int):					Minimum number of matches required.

	Returns:
		bool: True if at least n elements satisfy predicate, otherwise False.

	Examples:
		>>> at_least_n([1, 2, 3, 4, *[i for i in range(5, int(1e5))]], lambda x: x % 2 == 0, 2)
		True
		>>> at_least_n([1, 3, 5, 7], lambda x: x % 2 == 0, 1)
		False
	"""
	if n <= 0:
		return True
	count: int = 0
	for item in iterable:
		if predicate(item):
			count += 1
			if count >= n:
				return True
	return False

