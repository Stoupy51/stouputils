""" Common utilities shared by documentation generators (Sphinx, Zensical, etc.).

This module contains functions and helpers that are used by multiple documentation
backends, avoiding code duplication.
"""
# Imports
import os
from collections import defaultdict
from collections.abc import Callable

from ...config import StouputilsConfig as Cfg
from ...continuous_delivery import version_to_float
from ...decorators import simple_cache
from ...io.path import super_open
from ...print.message import info


# Functions
def check_base_dependencies() -> None:
	""" Check for each auto-docs requirement if it is installed.

	Raises:
		ImportError: If any requirement from ``Cfg.AUTO_DOCS_REQUIREMENTS`` is not installed
	"""
	import importlib
	for requirement in Cfg.AUTO_DOCS_REQUIREMENTS:
		try:
			importlib.import_module(requirement)
		except ImportError as e:
			requirements_str: str = " ".join(Cfg.AUTO_DOCS_REQUIREMENTS)
			raise ImportError(f"{requirement} is not installed. Please install the following requirements to use automatic_docs: '{requirements_str}'") from e

def download_asset(url: str, target_path: str) -> None:
	""" Download a file from a URL to a local path.

	Args:
		url         (str): URL to download from
		target_path (str): Local file path to save to
	"""
	import requests
	response = requests.get(url, timeout=30)
	response.raise_for_status()
	os.makedirs(os.path.dirname(target_path), exist_ok=True)
	with open(target_path, "wb") as f:
		f.write(response.content)

@simple_cache
def get_versions_from_github(github_user: str, github_repo: str, recent_minor_versions: int = 2) -> list[str]:
	""" Get list of versions from GitHub gh-pages branch.
	Only shows detailed versions for the last N minor versions, and keeps only
	the latest patch version for older minor versions.

	Args:
		github_user             (str): GitHub username
		github_repo             (str): GitHub repository name
		recent_minor_versions   (int): Number of recent minor versions to show all patches for (-1 for all).

	Returns:
		list[str]: List of versions, with 'latest' as first element
	"""
	import requests
	version_list: list[str] = []
	try:
		response = requests.get(f"https://api.github.com/repos/{github_user}/{github_repo}/contents?ref=gh-pages")
		if response.status_code == 200:
			contents: list[dict[str, str]] = response.json()
			all_versions: list[str] = sorted([
					d["name"].replace("v", "")
					for d in contents
					if d["type"] == "dir" and d["name"].startswith("v")
				], key=version_to_float, reverse=True
			)
			info(f"Found versions from GitHub: {all_versions}")

			# Group versions by major.minor
			minor_versions: dict[str, list[str]] = defaultdict(list)
			for version in all_versions:
				parts = version.split(".")
				if len(parts) >= 2:
					minor_key = f"{parts[0]}.{parts[1]}"
					minor_versions[minor_key].append(version)
			info(f"Grouped minor versions: {dict(minor_versions)}")

			# Get the sorted minor version keys
			sorted_minors = sorted(minor_versions.keys(), key=version_to_float, reverse=True)
			info(f"Sorted minor versions: {sorted_minors}")

			# Build final version list
			final_versions: list[str] = []
			for i, minor_key in enumerate(sorted_minors):
				if recent_minor_versions == -1 or i < recent_minor_versions:
					# Keep all patch versions for the recent minor versions
					final_versions.extend(minor_versions[minor_key])
				else:
					# Keep only the latest patch version for older minor versions
					final_versions.append(minor_versions[minor_key][0])

			version_list = ["latest", *final_versions]
	except Exception as e:
		info(f"Failed to get versions from GitHub: {e}")
		version_list = ["latest"]
	return version_list

def generate_version_selector(
	github_user: str,
	github_repo: str,
	get_versions_function: Callable[[str, str, int], list[str]] = get_versions_from_github,
	recent_minor_versions: int = 2,
) -> str:
	""" Generate the HTML version selector string from GitHub versions.

	Args:
		github_user            (str): GitHub username
		github_repo            (str): GitHub repository name
		get_versions_function  (Callable[[str, str, int], list[str]]): Function to get versions from GitHub
		recent_minor_versions  (int): Number of recent minor versions to show all patches for. Defaults to 2

	Returns:
		str: Markdown string with version links (e.g. ``**Versions**: latest, v1.0.0, ...``)
	"""
	version_list: list[str] = get_versions_function(github_user, github_repo, recent_minor_versions)
	version_links: list[str] = []
	for version in version_list:
		if version == "latest":
			version_links.append('<a href="../latest/">latest</a>')
		else:
			version_links.append(f'<a href="../v{version}/">v{version}</a>')
	return "\n\n**Versions**: " + ", ".join(version_links)

def generate_redirect_html(filepath: str) -> None:
	""" Generate HTML content for redirect page.

	Args:
		filepath (str): Path to the file where the HTML content should be written
	"""
	with super_open(filepath, "w", encoding="utf-8") as f:
		f.write("""<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta http-equiv="refresh" content="0;url=./latest/">
	<title>Redirecting...</title>
</head>
<body>
	<p>If you are not redirected automatically, <a href="./latest/">click here</a>.</p>
</body>
</html>
""")

