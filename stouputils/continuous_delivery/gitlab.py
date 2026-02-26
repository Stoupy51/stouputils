""" This module contains utilities for continuous delivery on GitLab.

- upload_to_gitlab: Upload the project to GitLab using the credentials and the configuration
  (make a release and upload the assets, handle existing tag, generate changelog, etc.)
"""

# Imports
from typing import Any
from urllib.parse import quote

from ..decorators import handle_error, measure_time
from .cd_utils import handle_response
from .release_common import (
	PlatformConfig,
	create_release,
	create_tag_on_branch,
	delete_resource,
	delete_resource_unconditional,
	generate_changelog,
	get_commits_since_tag,
	get_latest_tag,
	handle_existing_tag,
	log_success,
	upload_files,
	validate_required_keys,
)

# Constants
GITLAB_URL: str = "https://gitlab.com"


def validate_gitlab_credentials(credentials: dict[str, dict[str, str]], gitlab_url: str) -> tuple[str, dict[str, str]]:
	""" Get and validate GitLab credentials.

	Args:
		credentials: Credentials dictionary with 'gitlab' key containing 'api_key'
		gitlab_url:  Default GitLab instance URL
	Returns:
		tuple: (gitlab_url, headers dict)
	Raises:
		ValueError: If required keys are missing
	"""
	if "gitlab" not in credentials:
		raise ValueError(
			"The credentials file must contain a 'gitlab' key, which is a dictionary containing:\n"
			"- 'api_key': a Personal Access Token for the GitLab API\n"
			"- 'url' (optional): the GitLab instance URL"
		)
	validate_required_keys(credentials["gitlab"], ["api_key"], "gitlab credentials")

	api_key: str = credentials["gitlab"]["api_key"]
	url: str = credentials["gitlab"].get("url", gitlab_url).rstrip("/")
	headers: dict[str, str] = {"PRIVATE-TOKEN": api_key}
	return url, headers


def validate_gitlab_config(gitlab_config: dict[str, Any]) -> tuple[str, str, str, list[str]]:
	""" Validate GitLab configuration.

	Args:
		gitlab_config: Configuration dictionary
	Returns:
		tuple: (project_path, version, build_folder, endswith list)
	Raises:
		ValueError: If required keys are missing
	"""
	validate_required_keys(gitlab_config, ["project_path", "version", "build_folder"], "gitlab_config")

	return (
		gitlab_config["project_path"],
		gitlab_config["version"],
		gitlab_config["build_folder"],
		gitlab_config.get("endswith", []),
	)


def build_gitlab_config(
	gitlab_url: str,
	headers: dict[str, str],
	project_path: str,
	version: str,
	build_folder: str,
	endswith: list[str],
) -> PlatformConfig:
	""" Build a PlatformConfig for GitLab.

	Args:
		gitlab_url:   GitLab instance URL
		headers:      HTTP headers with authorization
		project_path: Full project path (e.g., "namespace/project")
		version:      Version to release
		build_folder: Path to build assets
		endswith:     File suffixes to upload
	Returns:
		PlatformConfig: Configuration for GitLab release
	"""
	encoded_path: str = quote(project_path, safe="")
	return PlatformConfig(
		base_url=gitlab_url,
		project_identifier=project_path,
		headers=headers,
		version=version,
		build_folder=build_folder,
		endswith=endswith,
		project_api_url=f"{gitlab_url}/api/v4/projects/{encoded_path}",
		web_url=gitlab_url,
		tag_api_path="/repository/tags",
		commit_api_path="/repository/commits",
		release_api_path="/releases",
		commit_url_path="/-/commit/",
		compare_url_path="/-/compare/",
		platform_name="GitLab",
	)


def delete_gitlab_release(config: PlatformConfig) -> None:
	""" Delete existing GitLab release for the configured version. """
	release_url: str = f"{config.project_api_url}/releases/v{config.version}"
	delete_resource(config, release_url, "release")


def delete_gitlab_tag(config: PlatformConfig) -> None:
	""" Delete existing GitLab tag for the configured version. """
	tag_url: str = f"{config.project_api_url}/repository/tags/v{config.version}"
	delete_resource_unconditional(config, tag_url, "tag")


def get_gitlab_sha(tag: dict[str, Any]) -> str:
	""" Extract SHA from a GitLab tag response. """
	return tag["commit"]["id"]


def get_gitlab_commit_date(commit: dict[str, Any]) -> str:
	""" Extract date from a GitLab commit response. """
	return str(commit["committed_date"])


def extract_gitlab_commit_data(commits: list[dict[str, Any]]) -> list[tuple[str, str]]:
	""" Extract (sha, message) tuples from GitLab commits. """
	return [(commit["id"], commit["message"]) for commit in commits]


def create_gitlab_tag(config: PlatformConfig) -> None:
	""" Create a new tag on GitLab. """
	tags_url: str = f"{config.project_api_url}/repository/tags"

	def create_tag_data(branch: str) -> dict[str, str]:
		return {"tag_name": f"v{config.version}", "ref": branch}

	create_tag_on_branch(config, tags_url, create_tag_data)


def create_gitlab_release(config: PlatformConfig, changelog: str) -> None:
	""" Create a new GitLab release.

	Args:
		config:    Platform configuration
		changelog: Changelog text for the release description
	"""
	release_data: dict[str, str] = {
		"tag_name": f"v{config.version}",
		"name": f"v{config.version}",
		"description": changelog,
	}
	create_release(config, release_data)


def upload_gitlab_assets(config: PlatformConfig) -> None:
	""" Upload release assets to GitLab via Package Registry.

	Args:
		config: Platform configuration
	"""
	import requests

	def upload_file(file_path: str, file_name: str) -> None:
		# Upload to Generic Package Registry
		package_url: str = f"{config.project_api_url}/packages/generic/release-assets/{config.version}/{file_name}"
		with open(file_path, "rb") as f:
			upload_response: requests.Response = requests.put(
				package_url,
				headers=config.headers,
				data=f.read()
			)
			handle_response(upload_response, f"Failed to upload {file_name} to package registry")

		# Get the download URL and link to release
		package_file_url: str = upload_response.json().get("file", {}).get("url", package_url)
		link_url: str = f"{config.project_api_url}/releases/v{config.version}/assets/links"
		link_data: dict[str, str] = {
			"name": file_name,
			"url": package_file_url,
			"link_type": "package"
		}
		link_response: requests.Response = requests.post(link_url, headers=config.headers, json=link_data)
		handle_response(link_response, f"Failed to link {file_name} to release")

	upload_files(config, upload_file)


@measure_time(message="Uploading to GitLab took")
@handle_error
def upload_to_gitlab(
	credentials: dict[str, Any],
	gitlab_config: dict[str, Any],
	gitlab_url: str = GITLAB_URL,
) -> str:
	""" Upload the project to GitLab using the credentials and the configuration.

	Args:
		credentials:   Credentials for the GitLab API
		gitlab_config: Configuration for the GitLab project
		gitlab_url:    GitLab instance URL (default: https://gitlab.com)
	Returns:
		str: Generated changelog text
	Examples:

	.. code-block:: python

		> upload_to_gitlab(
			credentials={
				"gitlab": {
					"api_key": "glpat-...",
				}
			},
			gitlab_config={
				"project_path": "DataScience/chestia",
				"version": "1.0.0",
				"build_folder": "dist",
				"endswith": [".tar.gz", ".whl"]
			},
			gitlab_url="https://gitlab.example.com"
		)
	"""
	import requests  # type: ignore  # noqa: F401

	# Validate inputs
	gitlab_url, headers = validate_gitlab_credentials(credentials, gitlab_url)
	project_path, version, build_folder, endswith = validate_gitlab_config(gitlab_config)

	# Build configuration
	config = build_gitlab_config(gitlab_url, headers, project_path, version, build_folder, endswith)

	# Handle existing tag
	tag_url: str = f"{config.project_api_url}/repository/tags/v{version}"
	can_create: bool = handle_existing_tag(config, tag_url, delete_gitlab_tag, delete_gitlab_release)

	# Get commits and generate changelog
	latest_tag_sha, latest_tag_version = get_latest_tag(config, get_gitlab_sha)
	commits: list[dict[str, Any]] = get_commits_since_tag(config, latest_tag_sha, get_gitlab_commit_date)
	commit_tuples = extract_gitlab_commit_data(commits)
	changelog: str = generate_changelog(commit_tuples, config, latest_tag_version)

	# Create release
	if can_create:
		create_gitlab_tag(config)
		create_gitlab_release(config, changelog)
		upload_gitlab_assets(config)
		log_success(config)

	return changelog

