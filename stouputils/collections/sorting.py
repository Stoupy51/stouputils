
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from typing import Any


# Functions
def sort_dict_keys[T](dictionary: dict[T, Any], order: list[T], reverse: bool = False) -> dict[T, Any]:
	""" Sort dictionary keys using a given order list (reverse optional)

	Args:
		dictionary: The dictionary to sort
		order:      The order list
		reverse:    Whether to sort in reverse order (given to sorted function which behaves differently than order.reverse())
	Returns:
		The sorted dictionary
	Examples:
		>>> sort_dict_keys({'b': 2, 'a': 1, 'c': 3}, order=["a", "b", "c"])
		{'a': 1, 'b': 2, 'c': 3}

		>>> sort_dict_keys({'b': 2, 'a': 1, 'c': 3}, order=["a", "b", "c"], reverse=True)
		{'c': 3, 'b': 2, 'a': 1}

		>>> sort_dict_keys({'b': 2, 'a': 1, 'c': 3, 'd': 4}, order=["c", "b"])
		{'c': 3, 'b': 2, 'a': 1, 'd': 4}
	"""
	return dict(sorted(dictionary.items(), key=lambda x: order.index(x[0]) if x[0] in order else len(order), reverse=reverse))

