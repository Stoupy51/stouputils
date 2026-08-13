""" Continuous delivery and deployment utilities.

This module provides tools for automating software delivery and deployment:

Key Features:
- GitHub release management and uploads
- GitLab release management and uploads
- PyPI package publishing utilities
- pyproject.toml file management
- Common CD/CI utilities
- Local git changelog generation

Components:

- :py:mod:`~cd_utils`: Common utilities for continuous delivery
- :py:mod:`~git`: Local git changelog utilities (:py:func:`~git.generate_local_changelog`, :py:func:`~git.changelog_cli`)
- :py:mod:`~github`: GitHub-specific utilities (:py:func:`~github.upload_to_github`)
- :py:mod:`~gitlab`: GitLab-specific utilities (:py:func:`~gitlab.upload_to_gitlab`)
- :py:mod:`~pypi`: PyPI publishing tools (:py:func:`~pypi.pypi_full_routine`)
- :py:mod:`~pyproject`: pyproject.toml file management
- :py:mod:`~stubs`: Stub file generation using pyright (:py:func:`~stubs.stubs_full_routine`)

"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .cd_utils import (
	clean_version as clean_version,
	format_changelog as format_changelog,
	handle_response as handle_response,
	load_credentials as load_credentials,
	parse_commit_message as parse_commit_message,
	version_to_float as version_to_float,
)
from .git import (
	changelog_cli as changelog_cli,
	create_url_formatter as create_url_formatter,
	detect_host_type as detect_host_type,
	generate_local_changelog as generate_local_changelog,
	get_commits_since_commit as get_commits_since_commit,
	get_commits_since_date as get_commits_since_date,
	get_commits_since_tag as get_commits_since_tag,
	get_latest_tag as get_latest_tag,
	get_local_tags as get_local_tags,
	get_remotes as get_remotes,
	parse_commit_log as parse_commit_log,
	parse_date_fallback as parse_date_fallback,
	parse_remote_url as parse_remote_url,
	run_git_command as run_git_command,
)
from .github import (
	GITHUB_API_URL as GITHUB_API_URL,
	build_github_config as build_github_config,
	create_github_release as create_github_release,
	create_github_tag as create_github_tag,
	delete_github_release as delete_github_release,
	delete_github_tag as delete_github_tag,
	extract_github_commit_data as extract_github_commit_data,
	get_github_commit_date as get_github_commit_date,
	get_github_sha as get_github_sha,
	upload_github_assets as upload_github_assets,
	upload_to_github as upload_to_github,
	validate_github_config as validate_github_config,
	validate_github_credentials as validate_github_credentials,
)
from .gitlab import (
	GITLAB_URL as GITLAB_URL,
	build_gitlab_config as build_gitlab_config,
	create_gitlab_release as create_gitlab_release,
	create_gitlab_tag as create_gitlab_tag,
	delete_gitlab_release as delete_gitlab_release,
	delete_gitlab_tag as delete_gitlab_tag,
	extract_gitlab_commit_data as extract_gitlab_commit_data,
	get_gitlab_commit_date as get_gitlab_commit_date,
	get_gitlab_sha as get_gitlab_sha,
	upload_gitlab_assets as upload_gitlab_assets,
	upload_to_gitlab as upload_to_gitlab,
	validate_gitlab_config as validate_gitlab_config,
	validate_gitlab_credentials as validate_gitlab_credentials,
)
from .pypi import (
	build_package as build_package,
	pypi_full_routine as pypi_full_routine,
	pypi_full_routine_using_uv as pypi_full_routine_using_uv,
	update_pip_and_required_packages as update_pip_and_required_packages,
	upload_package as upload_package,
)
from .pyproject import (
	format_toml_lists as format_toml_lists,
	get_version_from_pyproject as get_version_from_pyproject,
	increment_version_from_input as increment_version_from_input,
	increment_version_from_pyproject as increment_version_from_pyproject,
	read_pyproject as read_pyproject,
	write_pyproject as write_pyproject,
)
from .release_common import (
	PlatformConfig as PlatformConfig,
	check_existing_tag as check_existing_tag,
	create_release as create_release,
	create_tag_on_branch as create_tag_on_branch,
	delete_resource as delete_resource,
	delete_resource_unconditional as delete_resource_unconditional,
	fetch_commits_since_tag as fetch_commits_since_tag,
	fetch_latest_tag as fetch_latest_tag,
	generate_changelog as generate_changelog,
	handle_existing_tag as handle_existing_tag,
	log_success as log_success,
	paginate_api as paginate_api,
	prompt_delete_existing as prompt_delete_existing,
	publish_release as publish_release,
	upload_files as upload_files,
	validate_required_keys as validate_required_keys,
)
from .stubs import (
	clean_stubs_directory as clean_stubs_directory,
	generate_stubs as generate_stubs,
	stubs_full_routine as stubs_full_routine,
)

