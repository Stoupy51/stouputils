""" This module contains utilities for continuous delivery, such as loading credentials from a file.
It is mainly used by the :py:mod:`~stouputils.continuous_delivery.github` module.
"""

# Imports
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ..config import StouputilsConfig as Cfg
from ..decorators import handle_error
from ..io import clean_path, json_load
from ..print import warning

if TYPE_CHECKING:
	import requests

def parse_commit_message(message: str) -> tuple[str, str, str | None, bool]:
	""" Parse a commit message following the conventional commits convention.

	Convention format: <type>: <description> or <type>(<sub-category>): <description>

	Args:
		message	(str):	The commit message to parse (first line only)
	Returns:
		tuple[str, str, str | None, bool]:
			str:		The commit type (e.g., "Features", "Bug Fixes")
			str:		The commit description
			str | None:	The sub-category if present (e.g., "Project")
			bool:		True if it's a breaking change (indicated by !)
	Source:
		https://www.conventionalcommits.org/en/v1.0.0/

	>>> parse_commit_message("feat: Add new feature")
	('Features', 'Add new feature', None, False)
	>>> parse_commit_message("fix(API): Fix bug in endpoint")
	('Bug Fixes', 'Fix bug in endpoint', 'API', False)
	>>> parse_commit_message("feat!: Breaking change")
	('Features', 'Breaking change', None, True)
	>>> parse_commit_message("docs(README): Update documentation")
	('Documentation', 'Update documentation', 'README', False)
	>>> parse_commit_message("chore: Cleanup code")
	('Chores', 'Cleanup code', None, False)
	>>> parse_commit_message("refactor(core): Refactor module")
	('Code Refactoring', 'Refactor module', 'core', False)
	>>> parse_commit_message("No conventional format")
	('Other', 'No conventional format', None, False)
	>>> parse_commit_message("build!: Major build change")
	('Build System', 'Major build change', None, True)
	>>> parse_commit_message("wip: Work in progress")
	('Work in Progress', 'Work in progress', None, False)
	>>> parse_commit_message("unknown_type: Some description")
	('Unknowntype', 'Some description', None, False)
	"""
	# Default values for non-conventional commits
	if ":" not in message:
		return "Other", message.strip(), None, False

	commit_type_part, desc = message.split(":", 1)

	# Check for breaking change indicator (!)
	is_breaking: bool = False
	if "!" in commit_type_part:
		is_breaking = True
		commit_type_part = commit_type_part.replace("!", "")

	# Extract sub-category if present (e.g., 'feat(Project)' -> 'feat', 'Project')
	sub_category: str | None = None
	if "(" in commit_type_part and ")" in commit_type_part:
		# Extract the base type (before parentheses)
		commit_type: str = commit_type_part.split("(")[0].split("/")[0]
		# Extract the sub-category (between parentheses)
		sub_category = commit_type_part.split("(")[1].split(")")[0]
	else:
		# No sub-category, just clean the type
		commit_type = commit_type_part.split("/")[0]

	# Clean the type to only keep letters
	commit_type = "".join(c for c in commit_type.lower().strip() if c in "abcdefghijklmnopqrstuvwxyz")
	commit_type = Cfg.COMMIT_TYPES.get(commit_type, commit_type.title())

	return commit_type, desc.strip(), sub_category, is_breaking


def format_changelog(
	commits: list[tuple[str, str]],
	url_formatter: Callable[[str], str] | None = None,
	latest_tag_version: str | None = None,
	current_version: str | None = None,
	compare_url_formatter: Callable[[str, str], str] | None = None,
) -> str:
	""" Generate a changelog from a list of commits.

	Args:
		commits					(list[tuple[str, str]]):				List of (sha, message) tuples
		url_formatter			(Callable[[str], str] | None):			Function to format commit URLs.
			Takes a SHA and returns a URL string. If None, commits show only short SHA.
		latest_tag_version		(str | None):							Version of the previous tag for comparison link
		current_version			(str | None):							Current version being released
		compare_url_formatter	(Callable[[str, str], str] | None):		Function to format comparison URL.
			Takes (old_version, new_version) and returns a URL string.
	Returns:
		str: Generated changelog in Markdown format
	"""
	# Initialize the commit groups
	commit_groups: dict[str, list[tuple[str, str, str | None]]] = {}

	# Iterate over the commits and parse them
	for sha, message in commits:
		first_line: str = message.split("\n")[0]
		commit_type, desc, sub_category, is_breaking = parse_commit_message(first_line)

		# Prepend emoji if breaking change
		formatted_desc = f"[🚨] {desc}" if is_breaking else desc

		# Add the commit to the commit groups
		if commit_type not in commit_groups:
			commit_groups[commit_type] = []
		commit_groups[commit_type].append((formatted_desc, sha, sub_category))

	# Initialize the changelog
	changelog: str = "## Changelog\n\n"

	# Sort commit types by COMMIT_TYPES order, then alphabetically for unknown types
	commit_type_order: list[str] = list(Cfg.COMMIT_TYPES.values())
	sorted_commit_types = sorted(
		commit_groups.keys(),
		key=lambda x: (commit_type_order.index(x) if x in commit_type_order else len(commit_type_order), x)
	)

	# Iterate over the commit groups
	for commit_type in sorted_commit_types:
		changelog += f"### {commit_type}\n"

		# Group commits by sub-category
		sub_category_groups: dict[str | None, list[tuple[str, str, str | None]]] = {}
		for desc, sha, sub_category in commit_groups[commit_type]:
			if sub_category not in sub_category_groups:
				sub_category_groups[sub_category] = []
			sub_category_groups[sub_category].append((desc, sha, sub_category))

		# Sort sub-categories (None comes first, then alphabetical)
		sorted_sub_categories = sorted(
			sub_category_groups.keys(),
			key=lambda x: (x is None, x or "")
		)

		# Iterate over sub-categories
		for sub_category in sorted_sub_categories:
			# Add commits for this sub-category
			for desc, sha, _ in reversed(sub_category_groups[sub_category]):
				# Prepend sub-category to description if present
				if sub_category:
					words: list[str] = [
						word[0].upper() + word[1:]  # We don't use title() because we don't want to lowercase any letter
						for word in sub_category.replace("_", " ").split()
					]
					formatted_sub_category: str = " ".join(words)
					formatted_desc = f"[{formatted_sub_category}] {desc}"
				else:
					formatted_desc = desc

				# Format the commit reference with or without URL
				if url_formatter:
					commit_ref = f"[{sha[:7]}]({url_formatter(sha)})"
				else:
					commit_ref = f"({sha[:7]})"

				changelog += f"- {formatted_desc} {commit_ref}\n"

		changelog += "\n"

	# Add the full changelog link if there is a latest tag and comparison URL formatter
	if latest_tag_version and current_version and compare_url_formatter:
		changelog += f"**Full Changelog**: {compare_url_formatter(latest_tag_version, current_version)}\n"

	return changelog


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

