""" This module contains utilities for continuous delivery on GitHub.

- upload_to_github: Upload the project to GitHub using the credentials and the configuration
  (make a release and upload the assets, handle existing tag, generate changelog, etc.)

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/continuous_delivery/github_module.gif
  :alt: stouputils upload_to_github examples
"""

# Imports
import os
from typing import Any

import requests

from ..decorators import handle_error, measure_time
from ..io import clean_path
from ..print import info, progress, warning
from .cd_utils import clean_version, handle_response, version_to_float

# Constants
GITHUB_API_URL: str = "https://api.github.com"
PROJECT_ENDPOINT: str = f"{GITHUB_API_URL}/repos"
COMMIT_TYPES: dict[str, str] = {
	"feat":		"Features",
	"fix":		"Bug Fixes",
	"docs":		"Documentation",
	"style":	"Style",
	"refactor":	"Code Refactoring",
	"perf":		"Performance Improvements",
	"test":		"Tests",
	"build":	"Build System",
	"ci":		"CI/CD",
	"chore":	"Chores",
	"revert":	"Reverts",
	"uwu":		"UwU ༼ つ ◕_◕ ༽つ",
}

def validate_credentials(credentials: dict[str, dict[str, str]]) -> tuple[str, dict[str, str]]:
	""" Get and validate GitHub credentials

	Args:
		credentials (dict[str, dict[str, str]]):	Credentials for the GitHub API
	Returns:
		tuple[str, dict[str, str]]:
			str:			Owner (the username of the account to use)

			dict[str, str]:	Headers (for the requests to the GitHub API)
	"""
	if "github" not in credentials:
		raise ValueError(
			"The credentials file must contain a 'github' key, which is a dictionary containing a 'api_key' key"
			"(a PAT for the GitHub API: https://github.com/settings/tokens) "
			"and a 'username' key (the username of the account to use)"
		)
	if "api_key" not in credentials["github"]:
		raise ValueError(
			"The credentials file must contain a 'github' key, which is a dictionary containing a 'api_key' key"
			"(a PAT for the GitHub API: https://github.com/settings/tokens) "
			"and a 'username' key (the username of the account to use)"
		)
	if "username" not in credentials["github"]:
		raise ValueError(
			"The credentials file must contain a 'github' key, which is a dictionary containing a 'api_key' key"
			"(a PAT for the GitHub API: https://github.com/settings/tokens) "
			"and a 'username' key (the username of the account to use)"
		)

	api_key: str = credentials["github"]["api_key"]
	owner: str = credentials["github"]["username"]
	headers: dict[str, str] = {"Authorization": f"Bearer {api_key}"}
	return owner, headers

def validate_config(github_config: dict[str, Any]) -> tuple[str, str, str, list[str]]:
	""" Validate GitHub configuration

	Args:
		github_config (dict[str, str]):	Configuration for the GitHub project
	Returns:
		tuple[str, str, str, list[str]]:
			str: Project name on GitHub

			str: Version of the project

			str: Build folder path containing zip files to upload to the release

			list[str]: List of zip files to upload to the release
	"""
	if "project_name" not in github_config:
		raise ValueError(
			"The github_config file must contain a 'project_name' key, "
			"which is the name of the project on GitHub"
		)
	if "version" not in github_config:
		raise ValueError(
			"The github_config file must contain a 'version' key, "
			"which is the version of the project"
		)
	if "build_folder" not in github_config:
		raise ValueError(
			"The github_config file must contain a 'build_folder' key, "
			"which is the folder containing the build of the project "
			"(datapack and resourcepack zip files)"
		)

	project_name: str = github_config["project_name"]
	version: str = github_config["version"]
	build_folder: str = github_config["build_folder"]
	endswith: list[str] = github_config.get("endswith", [])

	return project_name, version, build_folder, endswith

def handle_existing_tag(owner: str, project_name: str, version: str, headers: dict[str, str]) -> bool:
	""" Check if tag exists and handle deletion if needed

	Args:
		owner			(str):				GitHub username
		project_name	(str):				Name of the GitHub repository
		version			(str):				Version to check for existing tag
		headers			(dict[str, str]):	Headers for GitHub API requests
	Returns:
		bool: True if the tag was deleted or if it was not found, False otherwise
	"""
	# Get the tag URL and check if it exists
	tag_url: str = f"{PROJECT_ENDPOINT}/{owner}/{project_name}/git/refs/tags/v{version}"
	response: requests.Response = requests.get(tag_url, headers=headers)

	# If the tag exists, ask the user if they want to delete it
	if response.status_code == 200:
		warning(f"A tag v{version} already exists. Do you want to delete it? (y/N): ")
		if input().lower() == "y":
			delete_existing_release(owner, project_name, version, headers)
			delete_existing_tag(tag_url, headers)
			return True
		else:
			return False
	return True

def delete_existing_release(owner: str, project_name: str, version: str, headers: dict[str, str]) -> None:
	""" Delete existing release for a version

	Args:
		owner			(str):				GitHub username
		project_name	(str):				Name of the GitHub repository
		version			(str):				Version of the release to delete
		headers			(dict[str, str]):	Headers for GitHub API requests
	"""
	# Get the release URL and check if it exists
	releases_url: str = f"{PROJECT_ENDPOINT}/{owner}/{project_name}/releases/tags/v{version}"
	release_response: requests.Response = requests.get(releases_url, headers=headers)

	# If the release exists, delete it
	if release_response.status_code == 200:
		release_id: int = release_response.json()["id"]
		delete_release: requests.Response = requests.delete(
			f"{PROJECT_ENDPOINT}/{owner}/{project_name}/releases/{release_id}",
			headers=headers
		)
		handle_response(delete_release, "Failed to delete existing release")
		info(f"Deleted existing release for v{version}")

def delete_existing_tag(tag_url: str, headers: dict[str, str]) -> None:
	""" Delete existing tag

	Args:
		tag_url	(str):				URL of the tag to delete
		headers	(dict[str, str]):	Headers for GitHub API requests
	"""
	delete_response: requests.Response = requests.delete(tag_url, headers=headers)
	handle_response(delete_response, "Failed to delete existing tag")
	info("Deleted existing tag")

def get_latest_tag(
	owner: str, project_name: str, version: str, headers: dict[str, str]
) -> tuple[str, str] | tuple[None, None]:
	""" Get latest tag information

	Args:
		owner			(str):				GitHub username
		project_name	(str):				Name of the GitHub repository
		version			(str):				Version to remove from the list of tags
		headers			(dict[str, str]):	Headers for GitHub API requests
	Returns:
		str|None: SHA of the latest tag commit, None if no tags exist
		str|None: Version number of the latest tag, None if no tags exist
	"""
	# Get the tags list
	tags_url: str = f"{PROJECT_ENDPOINT}/{owner}/{project_name}/tags"
	response = requests.get(tags_url, headers=headers)
	handle_response(response, "Failed to get tags")
	tags: list[dict[str, Any]] = response.json()

	# Remove the version from the list of tags and sort the tags by their float values
	tags = [tag for tag in tags if tag["name"] != f"v{version}"]
	tags.sort(key=lambda x: version_to_float(x.get("name", "0")), reverse=True)

	# If there are no tags, return None
	if len(tags) == 0:
		return None, None
	else:
		return tags[0]["commit"]["sha"], clean_version(tags[0]["name"], keep="ab")

def get_commits_since_tag(
	owner: str, project_name: str, latest_tag_sha: str|None, headers: dict[str, str]
) -> list[dict[str, Any]]:
	""" Get commits since last tag

	Args:
		owner			(str):				GitHub username
		project_name	(str):				Name of the GitHub repository
		latest_tag_sha	(str|None):			SHA of the latest tag commit
		headers			(dict[str, str]):	Headers for GitHub API requests
	Returns:
		list[dict]: List of commits since the last tag
	"""
	# Get the commits URL and parameters
	commits_url: str = f"{PROJECT_ENDPOINT}/{owner}/{project_name}/commits"
	commits_params: dict[str, str] = {"per_page": "100"}

	# Initialize tag_date as None
	tag_date: str|None = None	# type: ignore

	# If there is a latest tag, use it to get the commits since the tag date
	if latest_tag_sha:

		# Get the date of the latest tag
		tag_commit_url = f"{PROJECT_ENDPOINT}/{owner}/{project_name}/commits/{latest_tag_sha}"
		tag_response = requests.get(tag_commit_url, headers=headers)
		handle_response(tag_response, "Failed to get tag commit")
		tag_date: str = tag_response.json()["commit"]["committer"]["date"]

		# Use the date as the 'since' parameter to get all commits after that date
		commits_params["since"] = tag_date

	# Get the commits
	response = requests.get(commits_url, headers=headers, params=commits_params)
	handle_response(response, "Failed to get commits")
	commits: list[dict[str, Any]] = response.json()

	# Filter commits only if we have a tag_date
	if tag_date:
		commits = [c for c in commits if c["commit"]["committer"]["date"] != tag_date]
	return commits

def generate_changelog(
	commits: list[dict[str, Any]], owner: str, project_name: str, latest_tag_version: str|None, version: str
) -> str:
	""" Generate changelog from commits. They must follow the conventional commits convention.

	Convention format: <type>: <description>

	Args:
		commits				(list[dict]):	List of commits to generate changelog from
		owner				(str):			GitHub username
		project_name		(str):			Name of the GitHub repository
		latest_tag_version	(str|None):		Version number of the latest tag
		version				(str):			Current version being released
	Returns:
		str: Generated changelog text
	Source:
		https://www.conventionalcommits.org/en/v1.0.0/
	"""
	# Initialize the commit groups
	commit_groups: dict[str, list[tuple[str, str]]] = {}

	# Iterate over the commits
	for commit in commits:
		message: str = commit["commit"]["message"].split("\n")[0]
		sha: str = commit["sha"]

		# If the message contains a colon, split the message into a type and a description
		if ":" in message:
			commit_type, desc = message.split(":", 1)

			# Clean the type, ex: 'feat(hand)/refactor(feet)' -> 'feat'
			commit_type = commit_type.split('(')[0].split('/')[0]
			commit_type = "".join(c for c in commit_type.lower().strip() if c in "abcdefghijklmnopqrstuvwxyz")
			commit_type = COMMIT_TYPES.get(commit_type, commit_type.title())

			# Add the commit to the commit groups
			if commit_type not in commit_groups:
				commit_groups[commit_type] = []
			commit_groups[commit_type].append((desc.strip(), sha))

	# Initialize the changelog
	changelog: str = "## Changelog\n\n"

	# Iterate over the commit groups
	for commit_type in sorted(commit_groups.keys()):
		changelog += f"### {commit_type}\n"

		# Reverse the list to display the most recent commits in last
		for desc, sha in commit_groups[commit_type][::-1]:
			changelog += f"- {desc} ([{sha[:7]}](https://github.com/{owner}/{project_name}/commit/{sha}))\n"
		changelog += "\n"

	# Add the full changelog link if there is a latest tag and return the changelog
	if latest_tag_version:
		changelog += f"**Full Changelog**: https://github.com/{owner}/{project_name}/compare/v{latest_tag_version}...v{version}\n"
	return changelog

def create_tag(owner: str, project_name: str, version: str, headers: dict[str, str]) -> None:
	""" Create a new tag

	Args:
		owner			(str):				GitHub username
		project_name	(str):				Name of the GitHub repository
		version			(str):				Version for the new tag
		headers			(dict[str, str]):	Headers for GitHub API requests
	"""
	# Message and prepare urls
	progress(f"Creating tag v{version}")
	create_tag_url: str = f"{PROJECT_ENDPOINT}/{owner}/{project_name}/git/refs"
	latest_commit_url: str = f"{PROJECT_ENDPOINT}/{owner}/{project_name}/git/refs/heads/main"

	# Get the latest commit SHA
	commit_response: requests.Response = requests.get(latest_commit_url, headers=headers)
	handle_response(commit_response, "Failed to get latest commit")
	commit_sha: str = commit_response.json()["object"]["sha"]

	# Create the tag
	tag_data: dict[str, str] = {
		"ref": f"refs/tags/v{version}",
		"sha": commit_sha
	}
	response: requests.Response = requests.post(create_tag_url, headers=headers, json=tag_data)
	handle_response(response, "Failed to create tag")

def create_release(owner: str, project_name: str, version: str, changelog: str, headers: dict[str, str]) -> int:
	""" Create a new release

	Args:
		owner			(str):				GitHub username
		project_name	(str):				Name of the GitHub repository
		version			(str):				Version for the new release
		changelog		(str):				Changelog text for the release
		headers			(dict[str, str]):	Headers for GitHub API requests
	Returns:
		int: ID of the created release
	"""
	# Message and prepare urls
	progress(f"Creating release v{version}")
	release_url: str = f"{PROJECT_ENDPOINT}/{owner}/{project_name}/releases"
	release_data: dict[str, str|bool] = {
		"tag_name": f"v{version}",
		"name": f"{project_name} [v{version}]",
		"body": changelog,
		"draft": False,
		"prerelease": False
	}

	# Create the release and return the release ID
	response: requests.Response = requests.post(release_url, headers=headers, json=release_data)
	handle_response(response, "Failed to create release")
	return response.json()["id"]

def upload_assets(
	owner: str, project_name: str, release_id: int, build_folder: str, headers: dict[str, str], endswith: list[str]
) -> None:
	""" Upload release assets

	Args:
		owner			(str):				GitHub username
		project_name	(str):				Name of the GitHub repository
		release_id		(int):				ID of the release to upload assets to
		build_folder	(str):				Folder containing assets to upload
		headers			(dict[str, str]):	Headers for GitHub API requests
		endswith		(list[str]):		List of files to upload to the release
			(every file ending with one of these strings will be uploaded)
	"""
	endswith_tuple: tuple[str, ...] = tuple(endswith)

	# If there is no build folder, return
	if not build_folder:
		return
	progress("Uploading assets")

	# Get the release details
	release_url: str = f"{PROJECT_ENDPOINT}/{owner}/{project_name}/releases/{release_id}"
	response: requests.Response = requests.get(release_url, headers=headers)
	handle_response(response, "Failed to get release details")
	upload_url_template: str = response.json()["upload_url"]
	upload_url_base: str = upload_url_template.split("{", maxsplit=1)[0]

	# Iterate over the files in the build folder
	for file in os.listdir(build_folder):
		if file.endswith(endswith_tuple):
			file_path: str = f"{clean_path(build_folder)}/{file}"
			with open(file_path, "rb") as f:

				# Prepare the headers and params
				headers_with_content: dict[str, str] = {
					**headers,
					"Content-Type": "application/zip"
				}
				params: dict[str, str] = {"name": file}

				# Upload the file
				response: requests.Response = requests.post(
					upload_url_base,
					headers=headers_with_content,
					params=params,
					data=f.read()
				)
				handle_response(response, f"Failed to upload {file}")
				progress(f"Uploaded {file}")

@measure_time(progress, "Uploading to GitHub took")
@handle_error()
def upload_to_github(credentials: dict[str, Any], github_config: dict[str, Any]) -> str:
	""" Upload the project to GitHub using the credentials and the configuration

	Args:
		credentials		(dict[str, Any]):	Credentials for the GitHub API
		github_config	(dict[str, Any]):	Configuration for the GitHub project
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
	# Validate credentials and configuration
	owner, headers = validate_credentials(credentials)
	project_name, version, build_folder, endswith = validate_config(github_config)

	# Handle existing tag
	can_create: bool = handle_existing_tag(owner, project_name, version, headers)

	# Get the latest tag and commits since the tag
	latest_tag_sha, latest_tag_version = get_latest_tag(owner, project_name, version, headers)
	commits: list[dict[str, Any]] = get_commits_since_tag(owner, project_name, latest_tag_sha, headers)
	changelog: str = generate_changelog(commits, owner, project_name, latest_tag_version, version)

	# Create the tag and release if needed
	if can_create:
		create_tag(owner, project_name, version, headers)
		release_id: int = create_release(owner, project_name, version, changelog, headers)
		upload_assets(owner, project_name, release_id, build_folder, headers, endswith)
		info(f"Project '{project_name}' updated on GitHub!")
	return changelog

