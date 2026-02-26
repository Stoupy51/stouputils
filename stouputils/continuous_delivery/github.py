""" This module contains utilities for continuous delivery on GitHub.

- upload_to_github: Upload the project to GitHub using the credentials and the configuration
  (make a release and upload the assets, handle existing tag, generate changelog, etc.)

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/continuous_delivery/github_module.gif
  :alt: stouputils upload_to_github examples
"""

# Imports
from typing import Any

from ..decorators import handle_error, measure_time
from ..print.message import info, progress
from .cd_utils import handle_response
from .release_common import (
	PlatformConfig,
	create_release,
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
GITHUB_API_URL: str = "https://api.github.com"


def validate_github_credentials(credentials: dict[str, dict[str, str]]) -> tuple[str, dict[str, str]]:
	""" Get and validate GitHub credentials.

	Args:
		credentials: Credentials dictionary with 'github' key containing 'api_key' and 'username'
	Returns:
		tuple: (owner username, headers dict)
	Raises:
		ValueError: If required keys are missing
	"""
	if "github" not in credentials:
		raise ValueError(
			"The credentials file must contain a 'github' key, which is a dictionary containing:\n"
			"- 'api_key': a PAT for the GitHub API (https://github.com/settings/tokens)\n"
			"- 'username': the username of the account to use"
		)
	validate_required_keys(credentials["github"], ["api_key", "username"], "github credentials")

	api_key: str = credentials["github"]["api_key"]
	owner: str = credentials["github"]["username"]
	headers: dict[str, str] = {"Authorization": f"Bearer {api_key}"}
	return owner, headers


def validate_github_config(github_config: dict[str, Any]) -> tuple[str, str, str, list[str]]:
	""" Validate GitHub configuration.

	Args:
		github_config: Configuration dictionary
	Returns:
		tuple: (project_name, version, build_folder, endswith list)
	Raises:
		ValueError: If required keys are missing
	"""
	validate_required_keys(github_config, ["project_name", "version", "build_folder"], "github_config")

	return (
		github_config["project_name"],
		github_config["version"],
		github_config["build_folder"],
		github_config.get("endswith", []),
	)


def build_github_config(
	owner: str,
	headers: dict[str, str],
	project_name: str,
	version: str,
	build_folder: str,
	endswith: list[str],
	api_url: str,
) -> PlatformConfig:
	""" Build a PlatformConfig for GitHub.

	Args:
		owner:        GitHub username
		headers:      HTTP headers with authorization
		project_name: Name of the repository
		version:      Version to release
		build_folder: Path to build assets
		endswith:     File suffixes to upload
		api_url:      GitHub API URL
	Returns:
		PlatformConfig: Configuration for GitHub release
	"""
	project_identifier = f"{owner}/{project_name}"
	return PlatformConfig(
		base_url=api_url,
		project_identifier=project_identifier,
		headers=headers,
		version=version,
		build_folder=build_folder,
		endswith=endswith,
		project_api_url=f"{api_url}/repos/{project_identifier}",
		web_url="https://github.com",
		tag_api_path="/tags",
		commit_api_path="/commits",
		release_api_path="/releases",
		commit_url_path="/commit/",
		compare_url_path="/compare/",
		platform_name="GitHub",
	)


def delete_github_release(config: PlatformConfig) -> None:
	""" Delete existing GitHub release for the configured version. """
	import requests
	releases_url: str = f"{config.project_api_url}/releases/tags/v{config.version}"
	release_response: requests.Response = requests.get(releases_url, headers=config.headers)

	if release_response.status_code == 200:
		release_id: int = release_response.json()["id"]
		delete_url: str = f"{config.project_api_url}/releases/{release_id}"
		delete_response: requests.Response = requests.delete(delete_url, headers=config.headers)
		handle_response(delete_response, "Failed to delete existing release")
		info(f"Deleted existing release for v{config.version}")


def delete_github_tag(config: PlatformConfig) -> None:
	""" Delete existing GitHub tag for the configured version. """
	tag_url: str = f"{config.project_api_url}/git/refs/tags/v{config.version}"
	delete_resource_unconditional(config, tag_url, "tag")


def get_github_sha(tag: dict[str, Any]) -> str:
	""" Extract SHA from a GitHub tag response. """
	return tag["commit"]["sha"]


def get_github_commit_date(commit: dict[str, Any]) -> str:
	""" Extract date from a GitHub commit response. """
	return str(commit["commit"]["committer"]["date"])


def extract_github_commit_data(commits: list[dict[str, Any]]) -> list[tuple[str, str]]:
	""" Extract (sha, message) tuples from GitHub commits. """
	return [(commit["sha"], commit["commit"]["message"]) for commit in commits]


def create_github_tag(config: PlatformConfig) -> None:
	""" Create a new tag on GitHub. """
	import requests
	progress(f"Creating tag v{config.version}")
	create_tag_url: str = f"{config.project_api_url}/git/refs"
	latest_commit_url: str = f"{config.project_api_url}/git/refs/heads/main"

	commit_response: requests.Response = requests.get(latest_commit_url, headers=config.headers)
	handle_response(commit_response, "Failed to get latest commit")
	commit_sha: str = commit_response.json()["object"]["sha"]

	tag_data: dict[str, str] = {
		"ref": f"refs/tags/v{config.version}",
		"sha": commit_sha
	}
	response: requests.Response = requests.post(create_tag_url, headers=config.headers, json=tag_data)
	handle_response(response, "Failed to create tag")


def create_github_release(config: PlatformConfig, changelog: str) -> int:
	""" Create a new GitHub release and return its ID.

	Args:
		config:    Platform configuration
		changelog: Changelog text for the release body
	Returns:
		int: Release ID for asset uploads
	"""
	project_name = config.project_identifier.split("/")[-1]
	release_data: dict[str, str | bool] = {
		"tag_name": f"v{config.version}",
		"name": f"{project_name} [v{config.version}]",
		"body": changelog,
		"draft": False,
		"prerelease": False
	}
	response = create_release(config, release_data)
	return response["id"]


def upload_github_assets(config: PlatformConfig, release_id: int) -> None:
	""" Upload release assets to GitHub.

	Args:
		config:     Platform configuration
		release_id: ID of the release to upload assets to
	"""
	import requests

	# Get upload URL template
	release_url: str = f"{config.project_api_url}/releases/{release_id}"
	response: requests.Response = requests.get(release_url, headers=config.headers)
	handle_response(response, "Failed to get release details")
	upload_url_template: str = response.json()["upload_url"]
	upload_url_base: str = upload_url_template.split("{", maxsplit=1)[0]

	def upload_file(file_path: str, file_name: str) -> None:
		with open(file_path, "rb") as f:
			headers_with_content: dict[str, str] = {
				**config.headers,
				"Content-Type": "application/zip"
			}
			params: dict[str, str] = {"name": file_name}
			resp: requests.Response = requests.post(
				upload_url_base,
				headers=headers_with_content,
				params=params,
				data=f.read()
			)
			handle_response(resp, f"Failed to upload {file_name}")

	upload_files(config, upload_file)


@measure_time(message="Uploading to GitHub took")
@handle_error
def upload_to_github(
	credentials: dict[str, Any],
	github_config: dict[str, Any],
	api_url: str = GITHUB_API_URL,
) -> str:
	""" Upload the project to GitHub using the credentials and the configuration.

	Args:
		credentials:   Credentials for the GitHub API
		github_config: Configuration for the GitHub project
		api_url:       GitHub API URL (default: https://api.github.com)
	Returns:
		str: Generated changelog text
	Examples:

	.. code-block:: python

		> upload_to_github(
			credentials={
				"github": {
					"api_key": "ghp_...",
					"username": "Stoupy"
				}
			},
			github_config={
				"project_name": "stouputils",
				"version": "1.0.0",
				"build_folder": "build",
				"endswith": [".zip"]
			}
		)
	"""
	import requests  # type: ignore  # noqa: F401

	# Validate inputs
	owner, headers = validate_github_credentials(credentials)
	project_name, version, build_folder, endswith = validate_github_config(github_config)

	# Build configuration
	config = build_github_config(owner, headers, project_name, version, build_folder, endswith, api_url)

	# Handle existing tag
	tag_url: str = f"{config.project_api_url}/git/refs/tags/v{version}"
	can_create: bool = handle_existing_tag(config, tag_url, delete_github_tag, delete_github_release)

	# Get commits and generate changelog
	latest_tag_sha, latest_tag_version = get_latest_tag(config, get_github_sha)
	commits: list[dict[str, Any]] = get_commits_since_tag(config, latest_tag_sha, get_github_commit_date)
	commit_tuples = extract_github_commit_data(commits)
	changelog: str = generate_changelog(commit_tuples, config, latest_tag_version)

	# Create release
	if can_create:
		create_github_tag(config)
		release_id: int = create_github_release(config, changelog)
		upload_github_assets(config, release_id)
		log_success(config)

	return changelog

