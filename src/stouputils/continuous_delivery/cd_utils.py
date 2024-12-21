
# Imports
from ..print import *
from ..decorators import handle_error
from ..io import clean_path, super_json_load
import requests
import yaml
import os
from typing import Any

# Load credentials from file
@handle_error()
def load_credentials(credentials_path: str) -> dict[str, Any]:
	""" Load credentials from a JSON or YAML file into a dictionary

	The file must be in the following format (JSON example, you can imagine what the YAML format would be):
	```json
	{
	  "github": {
		"username": "Stoupy51",
		"api_key": "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXX"
	  },
	  ...
	}
	```

	Args:
		credentials_path (str): Path to the credentials file (.json or .yml)
	Returns:
		dict: Dictionary containing the credentials
	"""
	# Get the absolute path of the credentials file
	warning("Be cautious when loading credentials from external sources like this, as they might contain malicious code that could compromise your credentials without your knowledge")
	credentials_path = clean_path(credentials_path)

	# Check if the file exists
	if not os.path.exists(credentials_path):
		raise FileNotFoundError(f"Credentials file not found at '{credentials_path}'")
	
	# Load the file if it's a JSON file
	if credentials_path.endswith(".json"):
		return super_json_load(credentials_path)

	# Else, load the file if it's a YAML file
	elif credentials_path.endswith((".yml", ".yaml")):
		with open(credentials_path, "r") as f:
			return yaml.safe_load(f)
			
	# Else, raise an error
	else:
		raise ValueError("Credentials file must be .json or .yml format")


# Handle a response
def handle_response(response: requests.Response, error_message: str) -> None:
	""" Handle a response from the API
	Args:
		response		(requests.Response): The response from the API
		error_message	(str): The error message to raise if the response is not successful
	"""
	if response.status_code < 200 or response.status_code >= 300:
		try:
			raise ValueError(f"{error_message}, response code {response.status_code} with response {response.json()}")
		except requests.exceptions.JSONDecodeError:
			raise ValueError(f"{error_message}, response code {response.status_code} with response {response.text}")

