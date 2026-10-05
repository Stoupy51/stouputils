""" Common utilities shared by documentation generators (Sphinx, Zensical, etc.).

This module contains functions and helpers that are used by multiple documentation backends,
avoiding code duplication.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ...lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

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
			raise ImportError(
				f"{requirement} is not installed. "
				f"Please install the following requirements to use automatic_docs: '{requirements_str}'"
			) from e

def download_asset(url: str, target_path: str) -> None:
	""" Download a file from a URL to a local path.

	Args:
		url:         URL to download from
		target_path: Local file path to save to
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
	Only shows detailed versions for the last N minor versions,
	and keeps only the latest patch version for older minor versions.

	Args:
		github_user:           GitHub username
		github_repo:           GitHub repository name
		recent_minor_versions: Number of recent minor versions to show all patches for (-1 for all).
	Returns:
		List of versions, with 'latest' as first element
	"""
	import requests
	try:
		response = requests.get(f"https://api.github.com/repos/{github_user}/{github_repo}/contents?ref=gh-pages")
		if response.status_code != 200:
			return []
		contents: list[dict[str, str]] = response.json()
		all_versions: list[str] = sorted(
			[d["name"].replace("v", "") for d in contents if d["type"] == "dir" and d["name"].startswith("v")],
			key=version_to_float,
			reverse=True,
		)
		info(f"Found versions from GitHub: {all_versions}")
		return ["latest", *keep_recent_patches(all_versions, recent_minor_versions)]
	except Exception as e:
		info(f"Failed to get versions from GitHub: {e}")
		return ["latest"]

def keep_recent_patches(versions: list[str], recent_minor_versions: int) -> list[str]:
	""" Every patch of the most recent minor versions, then only the latest patch of each older minor version.

	Args:
		versions:              Versions sorted newest first, such as ``"1.3.1"``.
		recent_minor_versions: Number of minor versions keeping all their patches, -1 for all of them.
	"""
	minor_versions: dict[str, list[str]] = defaultdict(list)
	for version in versions:
		parts: list[str] = version.split(".")
		if len(parts) >= 2:
			minor_versions[f"{parts[0]}.{parts[1]}"].append(version)
	info(f"Grouped minor versions: {dict(minor_versions)}")
	sorted_minors: list[str] = sorted(minor_versions.keys(), key=version_to_float, reverse=True)
	info(f"Sorted minor versions: {sorted_minors}")
	kept: int = len(sorted_minors) if recent_minor_versions == -1 else recent_minor_versions
	return [version for i, minor_key in enumerate(sorted_minors) for version in minor_versions[minor_key][:None if i < kept else 1]]

def generate_version_selector(
	github_user: str,
	github_repo: str,
	get_versions_function: Callable[[str, str, int], list[str]] = get_versions_from_github,
	recent_minor_versions: int = 2,
) -> str:
	""" Generate the HTML version selector string from GitHub versions.

	Args:
		github_user:           GitHub username
		github_repo:           GitHub repository name
		get_versions_function: Function to get versions from GitHub
		recent_minor_versions: Number of recent minor versions to show all patches for. Defaults to 2
	Returns:
		Markdown string with version links (e.g. ``**Versions**: latest, v1.0.0, ...``), empty when no version is known
	"""
	version_list: list[str] = get_versions_function(github_user, github_repo, recent_minor_versions)
	if not version_list:
		return ""
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
		filepath: Path to the file where the HTML content should be written
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

