""" This module contains utilities for continuous delivery, such as loading credentials from a file.
It is mainly used by the `stouputils.continuous_delivery.github` module.
"""

# Imports
import os
from typing import TYPE_CHECKING, Any

from ..decorators import handle_error
from ..io import clean_path, json_load
from ..print import warning

if TYPE_CHECKING:
	import requests


# Load credentials from file
@handle_error()
def load_credentials(credentials_path: str) -> dict[str, Any]:
	""" Load credentials from a JSON or YAML file into a dictionary.

	Loads credentials from either a JSON or YAML file and returns them as a dictionary.
	The file must contain the required credentials in the appropriate format.

	Args:
		credentials_path (str): Path to the credentials file (.json or .yml)
	Returns:
		dict[str, Any]: Dictionary containing the credentials

	Example JSON format:

	.. code-block:: json

		{
			"github": {
				"username": "Stoupy51",
				"api_key": "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXX"
			}
		}

	Example YAML format:

	.. code-block:: yaml

		github:
			username: "Stoupy51"
			api_key: "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXX"
	"""
	# Get the absolute path of the credentials file
	warning(
		"Be cautious when loading credentials from external sources like this, "
		"as they might contain malicious code that could compromise your credentials without your knowledge"
	)
	credentials_path = clean_path(credentials_path)

	# Check if the file exists
	if not os.path.exists(credentials_path):
		raise FileNotFoundError(f"Credentials file not found at '{credentials_path}'")

	# Load the file if it's a JSON file
	if credentials_path.endswith(".json"):
		return json_load(credentials_path)

	# Else, load the file if it's a YAML file
	elif credentials_path.endswith((".yml", ".yaml")):
		from msgspec import yaml
		with open(credentials_path) as f:
			return yaml.decode(f.read())

	# Else, raise an error
	else:
		raise ValueError("Credentials file must be .json or .yml format")

# Handle a response
def handle_response(response: "requests.Response", error_message: str) -> None:
	""" Handle a response from the API by raising an error if the response is not successful (status code not in 200-299).

	Args:
		response		(requests.Response): The response from the API
		error_message	(str): The error message to raise if the response is not successful
	"""
	if response.status_code < 200 or response.status_code >= 300:
		import requests
		try:
			raise ValueError(f"{error_message}, response code {response.status_code} with response {response.json()}")
		except requests.exceptions.JSONDecodeError as e:
			raise ValueError(f"{error_message}, response code {response.status_code} with response {response.text}") from e

# Clean a version string
def clean_version(version: str, keep: str = "") -> str:
	""" Clean a version string

	Args:
		version	(str): The version string to clean
		keep	(str): The characters to keep in the version string
	Returns:
		str: The cleaned version string

	>>> clean_version("v1.e0.zfezf0.1.2.3zefz")
	'1.0.0.1.2.3'
	>>> clean_version("v1.e0.zfezf0.1.2.3zefz", keep="v")
	'v1.0.0.1.2.3'
	>>> clean_version("v1.2.3b", keep="ab")
	'1.2.3b'
	"""
	return "".join(c for c in version if c in "0123456789." + keep)

# Convert a version string to a float
def version_to_float(version: str, error: bool = True) -> Any:
	""" Converts a version string into a float for comparison purposes.
	The version string is expected to follow the format of major.minor.patch.something_else....,
	where each part is separated by a dot and can be extended indefinitely.
	Supports pre-release suffixes with numbers: devN/dN (dev), aN (alpha), bN (beta), rcN/cN (release candidate).
	Ordering: 1.0.0 > 1.0.0rc2 > 1.0.0rc1 > 1.0.0b2 > 1.0.0b1 > 1.0.0a2 > 1.0.0a1 > 1.0.0dev1

	Args:
		version (str): The version string to convert. (e.g. "v1.0.0.1.2.3", "v2.0.0b2", "v1.0.0rc1")
		error (bool): Return None on error instead of raising an exception
	Returns:
		float: The float representation of the version. (e.g. 0)

	>>> version_to_float("v1.0.0")
	1.0
	>>> version_to_float("v1.0.0.1")
	1.000000001
	>>> version_to_float("v2.3.7")
	2.003007
	>>> version_to_float("v1.0.0.1.2.3")
	1.0000000010020031
	>>> version_to_float("v2.0") > version_to_float("v1.0.0.1")
	True
	>>> version_to_float("v2.0.0") > version_to_float("v2.0.0rc") > version_to_float("v2.0.0b") > version_to_float("v2.0.0a") > version_to_float("v2.0.0dev")
	True
	>>> version_to_float("v1.0.0b") > version_to_float("v1.0.0a")
	True
	>>> version_to_float("v1.0.0") > version_to_float("v1.0.0b")
	True
	>>> version_to_float("v3.0.0a") > version_to_float("v2.9.9")
	True
	>>> version_to_float("v1.2.3b") < version_to_float("v1.2.3")
	True
	>>> version_to_float("1.0.0") == version_to_float("v1.0.0")
	True
	>>> version_to_float("2.0.0.0.0.0.1b") > version_to_float("2.0.0.0.0.0.1a")
	True
	>>> version_to_float("2.0.0.0.0.0.1") > version_to_float("2.0.0.0.0.0.1b")
	True
	>>> version_to_float("v1.0.0rc") == version_to_float("v1.0.0c")
	True
	>>> version_to_float("v1.0.0c") > version_to_float("v1.0.0b")
	True
	>>> version_to_float("v1.0.0d") < version_to_float("v1.0.0a")
	True
	>>> version_to_float("v1.0.0dev") < version_to_float("v1.0.0a")
	True
	>>> version_to_float("v1.0.0dev") == version_to_float("v1.0.0d")
	True
	>>> version_to_float("v1.0.0rc2") > version_to_float("v1.0.0rc1")
	True
	>>> version_to_float("v1.0.0b2") > version_to_float("v1.0.0b1")
	True
	>>> version_to_float("v1.0.0a2") > version_to_float("v1.0.0a1")
	True
	>>> version_to_float("v1.0.0dev2") > version_to_float("v1.0.0dev1")
	True
	>>> version_to_float("v1.0.0") > version_to_float("v1.0.0rc2") > version_to_float("v1.0.0rc1")
	True
	>>> version_to_float("v1.0.0rc1") > version_to_float("v1.0.0b2")
	True
	>>> version_to_float("v1.0.0b1") > version_to_float("v1.0.0a2")
	True
	>>> version_to_float("v1.0.0a1") > version_to_float("v1.0.0dev2")
	True
	>>> versions = ["v1.0.0", "v1.0.0rc2", "v1.0.0rc1", "v1.0.0b2", "v1.0.0b1", "v1.0.0a2", "v1.0.0a1", "v1.0.0dev2", "v1.0.0dev1"]
	>>> sorted_versions = sorted(versions, key=version_to_float, reverse=True)
	>>> sorted_versions == versions
	True
	"""
	try:
		# Check for pre-release suffixes and calculate suffix modifier
		# Suffixes are ordered from longest to shortest to avoid partial matches
		suffix_modifiers: dict[str, int] = {
			"dev": 4,  # dev is lowest
			"d": 4,    # d (dev) is lowest
			"a": 3,    # alpha
			"b": 2,    # beta
			"rc": 1,   # rc is highest pre-release
			"c": 1,    # c (release candidate)
		}
		suffix_type: int = 0  # 0 = no suffix, 1-4 = rc/c, b, a, dev/d
		suffix_number: int = 0

		# Check for suffixes with optional numbers
		for suffix, modifier in suffix_modifiers.items():
			if suffix in version:
				# Find the suffix position
				suffix_pos: int = version.rfind(suffix)
				after_suffix: str = version[suffix_pos + len(suffix):]

				# Check if there's a number after the suffix
				if after_suffix.isdigit():
					suffix_number = int(after_suffix)
					version = version[:suffix_pos]
				elif after_suffix == "":
					# Suffix at the end without number
					version = version[:suffix_pos]
				else:
					# Not a valid suffix match, continue searching
					continue

				# Found a valid suffix, set the type and break
				suffix_type = modifier
				break

		# Clean the version string by keeping only the numbers and dots
		version = clean_version(version)

		# Split the version string into parts
		version_parts: list[str] = version.split(".")
		total: float = 0.0
		multiplier: float = 1.0

		# Iterate over the parts and add lesser and lesser weight to each part
		for part in version_parts:
			total += int(part) * multiplier
			multiplier /= 1_000

		# Apply pre-release modifier
		# Pre-releases are represented as negative offsets from the base version
		# Lower suffix_type = closer to release (rc=1 is closest, dev=4 is furthest)
		# Higher suffix_number = closer to release within the same suffix type
		# Formula: base_version - (suffix_type * 1000 - suffix_number) * 1e-9
		# This ensures: 1.0.0 > 1.0.0rc2 > 1.0.0rc1 > 1.0.0b2 > 1.0.0a2 > 1.0.0dev2
		if suffix_type > 0:
			total -= (suffix_type * 1000 - suffix_number) * 1e-9

		return total
	except Exception as e:
		if error:
			raise ValueError(f"Invalid version string: '{version}'") from e
		else:
			return None # type: ignore

