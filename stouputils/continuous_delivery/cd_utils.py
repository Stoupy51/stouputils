""" This module contains utilities for continuous delivery, such as loading credentials from a file.
It is mainly used by the `stouputils.continuous_delivery.github` module.
"""

# Imports
import os
from typing import Any

import requests
import yaml

from ..decorators import handle_error
from ..io import clean_path, super_json_load
from ..print import warning


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
		return super_json_load(credentials_path)

	# Else, load the file if it's a YAML file
	elif credentials_path.endswith((".yml", ".yaml")):
		with open(credentials_path) as f:
			return yaml.safe_load(f)

	# Else, raise an error
	else:
		raise ValueError("Credentials file must be .json or .yml format")

# Handle a response
def handle_response(response: requests.Response, error_message: str) -> None:
	""" Handle a response from the API by raising an error if the response is not successful (status code not in 200-299).

	Args:
		response		(requests.Response): The response from the API
		error_message	(str): The error message to raise if the response is not successful
	"""
	if response.status_code < 200 or response.status_code >= 300:
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
def version_to_float(version: str) -> float:
	""" Converts a version string into a float for comparison purposes.
	The version string is expected to follow the format of major.minor.patch.something_else....,
	where each part is separated by a dot and can be extended indefinitely.

	Args:
		version (str): The version string to convert. (e.g. "v1.0.0.1.2.3")
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
	"""
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
	return total

