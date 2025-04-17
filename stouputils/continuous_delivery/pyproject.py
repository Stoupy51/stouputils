""" Utilities for reading, writing and managing pyproject.toml files.

This module provides functions to handle pyproject.toml files, including reading,
writing, version management and TOML formatting capabilities.

- read_pyproject: Read the pyproject.toml file.
- write_pyproject: Write to the pyproject.toml file.
- format_toml_lists: Format TOML lists with proper indentation.
- increment_version_from_input: Increment the patch version number.
- increment_version_from_pyproject: Increment version in pyproject.toml.
- get_version_from_pyproject: Get version from pyproject.toml.

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/continuous_delivery/pyproject_module.gif
  :alt: stouputils pyproject examples
"""

# Imports
from typing import Any

import toml

from ..io import super_open


def read_pyproject(pyproject_path: str) -> dict[str, Any]:
	""" Read the pyproject.toml file.

	Args:
		pyproject_path: Path to the pyproject.toml file.

	Returns:
		dict[str, Any]: The content of the pyproject.toml file.
	"""
	return toml.load(pyproject_path)


def format_toml_lists(content: str) -> str:
	""" Format TOML lists with indentation.

	Args:
		content (str): The content of the pyproject.toml file.

	Returns:
		str: The formatted content with properly indented lists.
	"""
	# Split the content into individual lines for processing
	lines: list[str] = content.split("\n")
	formatted_lines: list[str] = []

	for line in lines:
		# Check if line contains a list definition (has both [ ] and = characters)
		if "[" in line and "]" in line and "=" in line:
			# Only process simple lists that have one opening and closing bracket
			if line.count("[") == 1 and line.count("]") == 1:
				# Split into key and values parts
				key, values = line.split("=", 1)
				values = values.strip()

				# Check if values portion is a list
				if values.startswith("[") and values.endswith("]"):
					# Parse list values, removing empty entries
					values = [v.strip() for v in values[1:-1].split(",") if v.strip()]

					# For lists with multiple items, format across multiple lines
					if len(values) > 1:
						formatted_lines.append(f"{key}= [")
						for value in values:
							formatted_lines.append(f"\t{value},")
						formatted_lines.append("]")
					# For single item lists, keep on one line
					else:
						formatted_lines.append(f"{key}= [{values[0]}]")
					continue

		# Keep non-list lines unchanged
		formatted_lines.append(line)

	# Rejoin all lines with newlines
	return "\n".join(formatted_lines)


def write_pyproject(pyproject_path: str, pyproject_content: dict[str, Any]) -> None:
	""" Write to the pyproject.toml file with properly indented lists. """
	content: str = "\n" + toml.dumps(pyproject_content) + "\n"
	content = format_toml_lists(content)  # Apply formatting

	with super_open(pyproject_path, "w") as file:
		file.write(content)


def increment_version_from_input(version: str) -> str:
	""" Increment the version.

	Args:
		version: The version to increment. (ex: "0.1.0")

	Returns:
		str: The incremented version. (ex: "0.1.1")
	"""
	version_parts: list[str] = version.split(".")
	version_parts[-1] = str(int(version_parts[-1]) + 1)
	return ".".join(version_parts)

def increment_version_from_pyproject(pyproject_path: str) -> None:
	""" Increment the version in the pyproject.toml file.

	Args:
		pyproject_path: Path to the pyproject.toml file.
	"""
	pyproject_content: dict[str, Any] = read_pyproject(pyproject_path)
	pyproject_content["project"]["version"] = increment_version_from_input(pyproject_content["project"]["version"])
	write_pyproject(pyproject_path, pyproject_content)

def get_version_from_pyproject(pyproject_path: str) -> str:
	""" Get the version from the pyproject.toml file.

	Args:
		pyproject_path: Path to the pyproject.toml file.

	Returns:
		str: The version. (ex: "0.1.0")
	"""
	return read_pyproject(pyproject_path)["project"]["version"]

