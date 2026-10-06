""" 📝 Utilities for reading, writing and managing pyproject.toml files.

This module provides functions to handle pyproject.toml files, including reading,
writing, version management and TOML formatting capabilities.

- :py:func:`read_pyproject`: Read the pyproject.toml file.
- :py:func:`write_pyproject`: Write to the pyproject.toml file.
- :py:func:`format_toml_lists`: Format TOML lists with proper indentation.
- :py:func:`increment_version_from_input`: Increment the patch version number.
- :py:func:`increment_version_from_pyproject`: Increment version in pyproject.toml.
- :py:func:`get_version_from_pyproject`: Get version from pyproject.toml.
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import re
from typing import Any

from ..io.path import super_open

# Constants
ONE_LINE_LIST: re.Pattern[str] = re.compile(r"^([^=\[\]]*)=\s*\[([^\[\]]*)\]\s*$")
""" A ``key = [...]`` line holding a whole list, the only shape :func:`format_toml_lists` rewrites. """


def read_pyproject(pyproject_path: str) -> dict[str, Any]:
	""" Read the pyproject.toml file.

	Args:
		pyproject_path: Path to the pyproject.toml file.
	Returns:
		The content of the pyproject.toml file.
	>>> content = read_pyproject("pyproject.toml")
	>>> "." in content["project"]["version"]
	True
	"""
	from msgspec import toml
	with open(pyproject_path) as file:
		content = file.read()
	return toml.decode(content)


def format_toml_lists(content: str) -> str:
	""" Format TOML lists with indentation.

	Args:
		content: The content of the pyproject.toml file.
	Returns:
		The formatted content with properly indented lists.
	>>> toml_content = '''[project]
	... dependencies = [ "tqdm>=4.0.0", "requests>=2.20.0", "pyyaml>=6.0.0", ]'''
	>>> format_toml_lists(toml_content).replace("\\t", "    ") == '''[project]
	... dependencies = [
	...     "tqdm>=4.0.0",
	...     "requests>=2.20.0",
	...     "pyyaml>=6.0.0",
	... ]'''
	True
	>>> format_toml_lists('dependencies = []\\nreadme = "README.md"')
	'dependencies = []\\nreadme = "README.md"'
	"""
	formatted_lines: list[str] = []
	for line in content.split("\n"):
		match: re.Match[str] | None = ONE_LINE_LIST.match(line)
		if match is None:
			formatted_lines.append(line)
			continue
		key: str = match.group(1)
		values: list[str] = [value.strip() for value in match.group(2).split(",") if value.strip()]
		if len(values) > 1:
			formatted_lines += [f"{key}= [", *(f"\t{value}," for value in values), "]"]
		else:
			formatted_lines.append(f"{key}= [{''.join(values)}]")
	return "\n".join(formatted_lines)


def write_pyproject(path: str, content: dict[str, Any]) -> None:
	""" Write to the pyproject.toml file with properly indented lists.

	Args:
		path: Path to the pyproject.toml file.
		content: Content to write to the pyproject.toml file.
	"""
	from msgspec.toml import _import_tomli_w  # pyright: ignore[reportPrivateUsage]
	toml = _import_tomli_w()
	string: str = "\n" + toml.dumps(content) + "\n"
	string = format_toml_lists(string)  # Apply formatting

	with super_open(path, "w") as file:
		file.write(string)


def increment_version_from_input(version: str) -> str:
	""" Increment the version.

	Args:
		version: The version to increment. (ex: "0.1.0")
	Returns:
		The incremented version. (ex: "0.1.1")
	>>> increment_version_from_input("0.1.0")
	'0.1.1'
	>>> increment_version_from_input("1.2.9")
	'1.2.10'
	"""
	version_parts: list[str] = version.split(".")
	version_parts[-1] = str(int(version_parts[-1]) + 1)
	return ".".join(version_parts)

def increment_version_from_pyproject(path: str) -> None:
	""" Increment the version in the pyproject.toml file.

	Args:
		path: Path to the pyproject.toml file.

	.. code-block:: python

		import stouputils as stp

		stp.write_pyproject("pyproject.toml", {"project": {"name": "my_package", "version": "1.0.27"}})

		# Each call bumps the last number of the version
		for _ in range(3):
			stp.increment_version_from_pyproject("pyproject.toml")
			stp.info("Version is now", stp.get_version_from_pyproject("pyproject.toml"))

	.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/increment_version_from_pyproject.svg
		:alt: Terminal output of the example, the version going up by one each time
	"""
	pyproject_content: dict[str, Any] = read_pyproject(path)
	pyproject_content["project"]["version"] = increment_version_from_input(pyproject_content["project"]["version"])
	write_pyproject(path, pyproject_content)

def get_version_from_pyproject(path: str) -> str:
	""" Get the version from the pyproject.toml file.

	Args:
		path: Path to the pyproject.toml file.
	Returns:
		The version. (ex: "0.1.0")
	"""
	return read_pyproject(path)["project"]["version"]

