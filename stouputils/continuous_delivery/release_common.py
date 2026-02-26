""" This module contains shared utilities for release management on Git hosting platforms.

It provides common functionality used by both GitHub and GitLab modules.
"""

# Imports
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..io.path import clean_path
from ..print.message import info, progress, warning
from .cd_utils import clean_version, format_changelog, handle_response, version_to_float


@dataclass
class PlatformConfig:
	""" Configuration for a Git hosting platform release. """
	# API configuration
	base_url: str
	""" Base URL of the platform (e.g., "https://api.github.com" or "https://gitlab.com") """

	project_identifier: str
	""" Project identifier (e.g., "owner/repo" for GitHub, "namespace/project" for GitLab) """

	headers: dict[str, str]
	""" HTTP headers for API requests """

	# Version/build configuration
	version: str
	""" Version to release """

	build_folder: str
	""" Folder containing build assets """

	endswith: list[str]
	""" File suffixes to upload """

	# Platform-specific URL builders
	project_api_url: str
	""" API URL for project operations """

	web_url: str
	""" Web URL for user-facing links """

	# Platform-specific paths
	tag_api_path: str = ""
	""" API path for tags (e.g., "/repository/tags" or "/tags") """

	commit_api_path: str = ""
	""" API path for commits """

	release_api_path: str = "/releases"
	""" API path for releases """

	commit_url_path: str = ""
	""" URL path for commits in web UI (e.g., "/commit/" or "/-/commit/") """

	compare_url_path: str = ""
	""" URL path for compare in web UI """

	platform_name: str = ""
	""" Platform name for logging (e.g., "GitHub", "GitLab") """


def validate_required_keys(config: dict[str, Any], required_keys: list[str], config_name: str) -> None:
	""" Validate that required keys exist in a configuration dictionary.

	Args:
		config:        Configuration dictionary to validate
		required_keys: List of required key names
		config_name:   Name of the configuration (for error messages)
	Raises:
		ValueError: If any required key is missing
	"""
	for key in required_keys:
		if key not in config:
			raise ValueError(f"The {config_name} must contain a '{key}' key")


def check_existing_tag(config: PlatformConfig, tag_url: str) -> bool:
	""" Check if a tag exists.

	Args:
		config:  Platform configuration
		tag_url: URL to check for tag existence
	Returns:
		bool: True if tag exists
	"""
	import requests
	response: requests.Response = requests.get(tag_url, headers=config.headers)
	return response.status_code == 200


def prompt_delete_existing(
	config: PlatformConfig,
	delete_release_func: Callable[[PlatformConfig], None],
	delete_tag_func: Callable[[PlatformConfig], None],
) -> bool:
	""" Prompt user to delete existing tag and release.

	Args:
		config:              Platform configuration
		delete_release_func: Function to delete the release
		delete_tag_func:     Function to delete the tag
	Returns:
		bool: True if user chose to delete, False otherwise
	"""
	warning(f"A tag v{config.version} already exists. Do you want to delete it? (y/N): ")
	if input().lower() == "y":
		delete_release_func(config)
		delete_tag_func(config)
		return True
	return False


def handle_existing_tag(
	config: PlatformConfig,
	tag_url: str,
	delete_tag_func: Callable[[PlatformConfig], None],
	delete_release_func: Callable[[PlatformConfig], None],
) -> bool:
	""" Check if tag exists and handle deletion if needed.

	Args:
		config:              Platform configuration
		tag_url:             URL to check if tag exists
		delete_tag_func:     Function to delete the tag
		delete_release_func: Function to delete the release
	Returns:
		bool: True if we can proceed with creating the release
	"""
	if check_existing_tag(config, tag_url):
		return prompt_delete_existing(config, delete_release_func, delete_tag_func)
	return True


def get_latest_tag(
	config: PlatformConfig,
	sha_extractor: Callable[[dict[str, Any]], str],
) -> tuple[str, str] | tuple[None, None]:
	""" Get latest tag information.

	Args:
		config:        Platform configuration
		sha_extractor: Function to extract SHA from a tag dict
	Returns:
		tuple: (sha, version) or (None, None)
	"""
	import requests
	tags_url: str = f"{config.project_api_url}{config.tag_api_path}"
	response: requests.Response = requests.get(tags_url, headers=config.headers, params={"per_page": "100"})
	handle_response(response, "Failed to get tags")

	tags: list[dict[str, Any]] = response.json()
	# Remove the current version and sort by version number
	tags = [tag for tag in tags if tag["name"] != f"v{config.version}"]
	tags.sort(key=lambda x: version_to_float(x.get("name", "0")), reverse=True)

	if not tags:
		return None, None
	return sha_extractor(tags[0]), clean_version(tags[0]["name"], keep="ab")


def paginate_api(
	url: str,
	headers: dict[str, str],
	params: dict[str, str],
	per_page: int = 100,
) -> list[dict[str, Any]]:
	""" Paginate through all results from an API endpoint.

	Args:
		url:      API URL
		headers:  HTTP headers
		params:   Query parameters
		per_page: Number of items per page
	Returns:
		list: All results from all pages
	"""
	import requests
	results: list[dict[str, Any]] = []
	page = 1
	while True:
		page_params = params.copy()
		page_params["page"] = str(page)
		response = requests.get(url, headers=headers, params=page_params)
		handle_response(response, "Failed to get results")
		page_results = response.json()
		if not page_results:
			break
		results.extend(page_results)
		if len(page_results) < per_page:
			break
		page += 1
	return results


def get_commits_since_tag(
	config: PlatformConfig,
	latest_tag_sha: str | None,
	date_extractor: Callable[[dict[str, Any]], str],
) -> list[dict[str, Any]]:
	""" Get commits since last tag.

	Args:
		config:         Platform configuration
		latest_tag_sha: SHA of the latest tag commit (or None)
		date_extractor: Function to extract date from a commit dict
	Returns:
		list: List of commits since the tag
	"""
	import requests
	commits_url: str = f"{config.project_api_url}{config.commit_api_path}"
	commits_params: dict[str, str] = {"per_page": "100"}
	tag_date: str | None = None

	if latest_tag_sha:
		tag_commit_url = f"{commits_url}/{latest_tag_sha}"
		tag_response = requests.get(tag_commit_url, headers=config.headers)
		handle_response(tag_response, "Failed to get tag commit")
		tag_date = date_extractor(tag_response.json())
		commits_params["since"] = tag_date

	commits = paginate_api(commits_url, config.headers, commits_params)

	if tag_date:
		commits = [c for c in commits if date_extractor(c) != tag_date]
	return commits


def generate_changelog(
	commits: list[tuple[str, str]],
	config: PlatformConfig,
	latest_tag_version: str | None,
) -> str:
	""" Generate changelog from commits using platform-specific URL patterns.

	Args:
		commits:            List of (sha, message) tuples
		config:             Platform configuration
		latest_tag_version: Previous version for comparison link
	Returns:
		str: Generated changelog text
	"""
	def url_formatter(sha: str) -> str:
		return f"{config.web_url}/{config.project_identifier}{config.commit_url_path}{sha}"

	def compare_url_formatter(old_version: str, new_version: str) -> str:
		return f"{config.web_url}/{config.project_identifier}{config.compare_url_path}v{old_version}...v{new_version}"

	return format_changelog(
		commits=commits,
		url_formatter=url_formatter,
		latest_tag_version=latest_tag_version,
		current_version=config.version,
		compare_url_formatter=compare_url_formatter,
	)


def upload_files(
	config: PlatformConfig,
	upload_func: Callable[[str, str], None],
) -> None:
	""" Upload files matching the specified suffixes.

	Args:
		config:      Platform configuration
		upload_func: Function to upload a single file (takes file path and file name)
	"""
	endswith_tuple: tuple[str, ...] = tuple(config.endswith)

	if not config.build_folder or not os.path.exists(config.build_folder):
		return

	files_to_upload: list[str] = [
		f for f in os.listdir(config.build_folder)
		if f.endswith(endswith_tuple)
	]

	if not files_to_upload:
		return

	progress("Uploading assets")
	for file in files_to_upload:
		file_path: str = f"{clean_path(config.build_folder)}/{file}"
		upload_func(file_path, file)
		progress(f"Uploaded {file}")


def log_success(config: PlatformConfig) -> None:
	""" Log a success message after upload.

	Args:
		config: Platform configuration
	"""
	info(f"Project '{config.project_identifier}' updated on {config.platform_name}!")


def delete_resource(config: PlatformConfig, url: str, resource_name: str) -> None:
	""" Delete a resource (release or tag) by its URL if it exists.

	Args:
		config:        Platform configuration
		url:           Full URL of the resource
		resource_name: Name for logging (e.g., "release", "tag")
	"""
	import requests
	response: requests.Response = requests.get(url, headers=config.headers)
	if response.status_code == 200:
		delete_response: requests.Response = requests.delete(url, headers=config.headers)
		handle_response(delete_response, f"Failed to delete existing {resource_name}")
		info(f"Deleted existing {resource_name} for v{config.version}")


def delete_resource_unconditional(config: PlatformConfig, url: str, resource_name: str) -> None:
	""" Delete a resource without checking if it exists first.

	Args:
		config:        Platform configuration
		url:           Full URL of the resource
		resource_name: Name for logging (e.g., "release", "tag")
	"""
	import requests
	delete_response: requests.Response = requests.delete(url, headers=config.headers)
	handle_response(delete_response, f"Failed to delete existing {resource_name}")
	info(f"Deleted existing {resource_name}")


def create_tag_on_branch(
	config: PlatformConfig,
	tags_url: str,
	create_tag_data: Callable[[str], dict[str, str]],
	branches: list[str] | None = None,
) -> None:
	""" Create a tag, trying multiple branch names if needed.

	Args:
		config:          Platform configuration
		tags_url:        API URL for creating tags
		create_tag_data: Function to create tag request data given a branch name
		branches:        List of branch names to try (default: ["main", "master"])
	"""
	import requests
	if branches is None:
		branches = ["main", "master"]

	progress(f"Creating tag v{config.version}")

	response: requests.Response | None = None
	for branch in branches:
		tag_data = create_tag_data(branch)
		response = requests.post(tags_url, headers=config.headers, json=tag_data)
		if response.status_code not in (400, 404):
			break

	if response is not None:
		handle_response(response, "Failed to create tag")


def create_release(
	config: PlatformConfig,
	release_data: dict[str, Any],
) -> dict[str, Any]:
	""" Create a release.

	Args:
		config:       Platform configuration
		release_data: Release request data
	Returns:
		dict: Response JSON from the API
	"""
	import requests
	progress(f"Creating release v{config.version}")
	release_url: str = f"{config.project_api_url}{config.release_api_path}"

	response: requests.Response = requests.post(release_url, headers=config.headers, json=release_data)
	handle_response(response, "Failed to create release")
	return response.json()
