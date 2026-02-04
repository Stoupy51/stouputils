""" This module contains utilities for generating changelogs from local git repositories.

- changelog_cli: CLI interface for generating changelogs from local git history
- get_commits_since_tag: Get all commits since a specific tag
- get_commits_since_date: Get all commits since a specific date
- get_commits_since_commit: Get all commits since a specific commit
- parse_remote_url: Parse a git remote URL to extract the base URL for commit links

Usage:
	stouputils changelog [tag|date|commit] [value] [--remote <remote>] [-o <file>]

Examples:
	stouputils changelog                          # Uses latest tag (default)
	stouputils changelog tag v1.9.0               # All commits since tag v1.9.0
	stouputils changelog date 2026/01/05          # All commits since date
	stouputils changelog commit 847b27e           # All commits since commit
	stouputils changelog --remote origin          # Use origin remote for commit URLs
	stouputils changelog -o CHANGELOG.md          # Output to file
"""

# Imports
import argparse
import re
import subprocess
from collections.abc import Callable
from datetime import datetime

from ..decorators import handle_error
from ..io import super_open
from ..print import info, progress, warning
from .cd_utils import clean_version, format_changelog, version_to_float


def run_git_command(args: list[str], cwd: str | None = None) -> str:
	""" Run a git command and return the output.

	Args:
		args	(list[str]):	Git command arguments (without 'git' prefix)
		cwd		(str | None):	Working directory for the command
	Returns:
		str:	Command output (stdout)
	Raises:
		RuntimeError:	If the git command fails
	"""
	cmd: list[str] = ["git", *args]
	result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, encoding="utf-8", errors="replace")
	if result.returncode != 0:
		raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{result.stderr}")
	return result.stdout.strip() if result.stdout else ""


def get_local_tags(cwd: str | None = None) -> list[tuple[str, str]]:
	""" Get all tags from the local git repository, sorted by version.

	Args:
		cwd	(str | None):	Working directory for the git command
	Returns:
		list[tuple[str, str]]:	List of (tag_name, commit_sha) tuples, sorted by version (newest first)
	"""
	try:
		output: str = run_git_command(["tag", "--format=%(refname:short) %(objectname:short)"], cwd=cwd)
	except RuntimeError:
		return []
	if not output:
		return []

	tags: list[tuple[str, str]] = []
	for line in output.split("\n"):
		if line.strip():
			parts = line.strip().split(" ", 1)
			if len(parts) == 2:
				tags.append((parts[0], parts[1]))

	# Sort by version (newest first)
	tags.sort(key=lambda x: version_to_float(x[0], error=False) or 0, reverse=True)
	return tags


def get_latest_tag(cwd: str | None = None, exclude_version: str | None = None) -> tuple[str, str] | tuple[None, None]:
	""" Get the latest tag from the local git repository.

	Args:
		cwd				(str | None):	Working directory for the git command
		exclude_version	(str | None):	Version to exclude from the search
	Returns:
		tuple[str, str] | tuple[None, None]:	(tag_name, commit_sha) or (None, None) if no tags exist
	"""
	tags: list[tuple[str, str]] = get_local_tags(cwd)

	# Exclude specified version if provided
	if exclude_version:
		clean_exclude: str = clean_version(exclude_version, keep="ab")
		tags = [t for t in tags if clean_version(t[0], keep="ab") != clean_exclude]

	if not tags:
		return None, None
	return tags[0]


def get_commits_since_tag(tag: str, cwd: str | None = None) -> list[tuple[str, str]]:
	""" Get all commits since a specific tag.

	Args:
		tag	(str):			Tag name to start from (exclusive)
		cwd	(str | None):	Working directory for the git command
	Returns:
		list[tuple[str, str]]:	List of (sha, message) tuples
	"""
	try:
		# Get commits from tag to HEAD
		output: str = run_git_command(
			["log", f"{tag}..HEAD", "--format=%H%x00%s%x00%b%x1E"],
			cwd=cwd
		)
		return parse_commit_log(output)
	except RuntimeError as e:
		warning(f"Failed to get commits since tag '{tag}': {e}")
		return []


def get_commits_since_date(date_str: str, cwd: str | None = None) -> list[tuple[str, str]]:
	""" Get all commits since a specific date.

	Args:
		date_str	(str):			Date string (supports multiple formats via dateutil)
		cwd			(str | None):	Working directory for the git command
	Returns:
		list[tuple[str, str]]:	List of (sha, message) tuples
	"""
	# Parse the date using dateutil for flexibility
	try:
		from dateutil import parser as date_parser
		parsed_date = date_parser.parse(date_str)
		# Format as ISO 8601 for git
		iso_date: str = parsed_date.strftime("%Y-%m-%dT%H:%M:%S")
	except ImportError:
		# Fallback: try common formats manually
		iso_date: str = parse_date_fallback(date_str)
	except Exception as e:
		raise ValueError(f"Could not parse date '{date_str}': {e}") from e

	try:
		output: str = run_git_command(
			["log", f"--since={iso_date}", "--format=%H%x00%s%x00%b%x1E"],
			cwd=cwd
		)
		return parse_commit_log(output)
	except RuntimeError as e:
		warning(f"Failed to get commits since date '{date_str}': {e}")
		return []


def get_commits_since_commit(commit_sha: str, cwd: str | None = None) -> list[tuple[str, str]]:
	""" Get all commits since a specific commit (exclusive).

	Args:
		commit_sha	(str):			Commit SHA to start from (this commit is excluded)
		cwd			(str | None):	Working directory for the git command
	Returns:
		list[tuple[str, str]]:	List of (sha, message) tuples
	"""
	try:
		output = run_git_command(
			["log", f"{commit_sha}..HEAD", "--format=%H%x00%s%x00%b%x1E"],
			cwd=cwd
		)
		return parse_commit_log(output)
	except RuntimeError as e:
		warning(f"Failed to get commits since commit '{commit_sha}': {e}")
		return []


def parse_date_fallback(date_str: str) -> str:
	""" Parse a date string without dateutil, trying common formats.

	Args:
		date_str	(str):	Date string to parse
	Returns:
		str:	ISO 8601 formatted date string
	Raises:
		ValueError:	If the date cannot be parsed

	>>> parse_date_fallback("2026/01/15")
	'2026-01-15T00:00:00'
	>>> parse_date_fallback("2026-01-15")
	'2026-01-15T00:00:00'
	>>> parse_date_fallback("2026-01-15 14:30:00")
	'2026-01-15T14:30:00'
	>>> parse_date_fallback("2026-01-15T14:30:00")
	'2026-01-15T14:30:00'
	"""
	formats: list[str] = [
		"%Y/%m/%d",
		"%Y-%m-%d",
		"%d/%m/%Y",
		"%d-%m-%Y",
		"%Y/%m/%d %H:%M:%S",
		"%Y-%m-%d %H:%M:%S",
		"%Y-%m-%dT%H:%M:%S",
	]
	for fmt in formats:
		try:
			parsed = datetime.strptime(date_str, fmt)
			return parsed.strftime("%Y-%m-%dT%H:%M:%S")
		except ValueError:
			continue
	raise ValueError(f"Could not parse date '{date_str}'. Supported formats: YYYY/MM/DD, YYYY-MM-DD")


def parse_commit_log(output: str) -> list[tuple[str, str]]:
	""" Parse git log output into a list of (sha, message) tuples.

	Args:
		output	(str):	Output from git log command
	Returns:
		list[tuple[str, str]]:	List of (sha, full_message) tuples
	"""
	if not output:
		return []

	commits: list[tuple[str, str]] = []
	# Split by record separator (0x1E)
	for record in output.split("\x1E"):
		record = record.strip()
		if not record:
			continue
		# Split by null character (0x00)
		parts: list[str] = record.split("\x00")
		if len(parts) >= 2:
			sha: str = parts[0]
			subject: str = parts[1]
			body: str = parts[2] if len(parts) > 2 else ""
			full_message: str = f"{subject}\n{body}".strip() if body else subject
			commits.append((sha, full_message))
	return commits


def get_remotes(cwd: str | None = None) -> dict[str, str]:
	""" Get all git remotes and their URLs.

	Args:
		cwd	(str | None):	Working directory for the git command
	Returns:
		dict[str, str]:	Dictionary mapping remote names to their push URLs
	"""
	try:
		output = run_git_command(["remote", "-v"], cwd=cwd)
	except RuntimeError:
		return {}

	remotes: dict[str, str] = {}
	for line in output.split("\n"):
		if "(push)" in line:
			parts: list[str] = line.split()
			if len(parts) >= 2:
				name: str = parts[0]
				url: str = parts[1]
				remotes[name] = url
	return remotes


def parse_remote_url(remote_url: str) -> tuple[str, str, str] | None:
	""" Parse a git remote URL to extract hosting info.

	Supports:
	- SSH format: git@github.com:user/repo.git
	- SSH format: git@gitlab.example.com:group/repo.git
	- HTTPS format: https://github.com/user/repo.git
	- HTTPS format: https://gitlab.example.com/group/repo.git

	Args:
		remote_url	(str):	Git remote URL
	Returns:
		tuple[str, str, str] | None:	(host_type, base_url, repo_path) or None if cannot parse
			host_type:	host_type: "github", "gitlab", or "unknown"
			base_url:	Base URL for the repository (e.g., "https://github.com/user/repo")
			repo_path:	Repository path (e.g., "user/repo")

	>>> parse_remote_url("git@github.com:Stoupy51/stouputils.git")
	('github', 'https://github.com/Stoupy51/stouputils', 'Stoupy51/stouputils')
	>>> parse_remote_url("https://github.com/Stoupy51/stouputils.git")
	('github', 'https://github.com/Stoupy51/stouputils', 'Stoupy51/stouputils')
	>>> parse_remote_url("git@gitlab.example.com:group/project.git")
	('gitlab', 'https://gitlab.example.com/group/project', 'group/project')
	>>> parse_remote_url("https://gitlab.company.com/team/repo.git")
	('gitlab', 'https://gitlab.company.com/team/repo', 'team/repo')
	>>> parse_remote_url("git@custom-server.com:user/repo.git")
	('gitlab', 'https://custom-server.com/user/repo', 'user/repo')
	>>> parse_remote_url("invalid-url") is None
	True
	"""
	# SSH format: git@host:path.git
	ssh_match = re.match(r"git@([^:]+):(.+?)(?:\.git)?$", remote_url)
	if ssh_match:
		host = ssh_match.group(1)
		path = ssh_match.group(2)
		host_type = _detect_host_type(host)
		base_url = f"https://{host}/{path}"
		return host_type, base_url, path

	# HTTPS format: https://host/path.git
	https_match = re.match(r"https?://([^/]+)/(.+?)(?:\.git)?$", remote_url)
	if https_match:
		host = https_match.group(1)
		path = https_match.group(2)
		host_type = _detect_host_type(host)
		base_url = f"https://{host}/{path}"
		return host_type, base_url, path

	return None


def _detect_host_type(host: str) -> str:
	""" Detect the type of git hosting service from hostname.

	Args:
		host	(str):	Hostname (e.g., "github.com", "gitlab.example.com")
	Returns:
		str:	"github", "gitlab", or "unknown"

	>>> _detect_host_type("github.com")
	'github'
	>>> _detect_host_type("gitlab.com")
	'gitlab'
	>>> _detect_host_type("gitlab.example.com")
	'gitlab'
	>>> _detect_host_type("custom-server.com")
	'gitlab'
	>>> _detect_host_type("my-github-mirror.org")
	'github'
	"""
	host_lower: str = host.lower()
	if "github" in host_lower:
		return "github"
	elif "gitlab" in host_lower:
		return "gitlab"
	else:
		# Default to GitLab-style URLs for unknown hosts (more common for self-hosted)
		return "gitlab"


def create_url_formatter(remote_url: str) -> tuple[Callable[[str], str], Callable[[str, str], str]] | None:
	""" Create URL formatter functions for a git remote.

	Args:
		remote_url	(str):	Git remote URL
	Returns:
		tuple[Callable, Callable] | None:	(commit_url_formatter, compare_url_formatter) or None
	"""
	parsed: tuple[str, str, str] | None = parse_remote_url(remote_url)
	if not parsed:
		return None

	host_type, base_url, _ = parsed

	if host_type == "github":
		def commit_formatter(sha: str) -> str:
			return f"{base_url}/commit/{sha}"
		def compare_formatter(old_version: str, new_version: str) -> str:
			return f"{base_url}/compare/v{old_version}...v{new_version}"

	# GitLab or unknown (use GitLab format)
	else:
		def commit_formatter(sha: str) -> str:
			return f"{base_url}/-/commit/{sha}"
		def compare_formatter(old_version: str, new_version: str) -> str:
			return f"{base_url}/-/compare/v{old_version}...v{new_version}"

	return commit_formatter, compare_formatter


def generate_local_changelog(
	mode: str = "tag",
	value: str | None = None,
	remote: str | None = None,
	cwd: str | None = None,
) -> str:
	""" Generate a changelog from local git history.

	Args:
		mode	(str):			Mode for selecting commits - "tag", "date", or "commit"
		value	(str | None):	Value for the mode (tag name, date, or commit SHA).
			If None and mode is "tag", uses the latest tag.
		remote	(str | None):	Remote name to use for commit URLs. If None, no URLs are generated.
		cwd		(str | None):	Working directory for git commands
	Returns:
		str:	Generated changelog in Markdown format
	"""
	# Get commits based on mode
	latest_tag_version: str | None = None

	commits: list[tuple[str, str]] = []

	if mode == "tag":
		if value:
			tag_name = value
		else:
			# Use the latest tag
			tag_result = get_latest_tag(cwd=cwd)
			if tag_result[0] is None:
				info("No tags found in the repository. Showing all commits.")
				# Get all commits
				try:
					output = run_git_command(["log", "--format=%H%x00%s%x00%b%x1E"], cwd=cwd)
					commits = parse_commit_log(output)
				except RuntimeError:
					commits = []
				tag_name = None
			else:
				tag_name = tag_result[0]

		if tag_name:
			commits = get_commits_since_tag(tag_name, cwd=cwd)
			latest_tag_version = clean_version(tag_name, keep="ab")
			progress(f"Found {len(commits)} commits since tag '{tag_name}'")

	elif mode == "date":
		if not value:
			raise ValueError("Date value is required for 'date' mode")
		commits = get_commits_since_date(value, cwd=cwd)
		progress(f"Found {len(commits)} commits since {value}")

	elif mode == "commit":
		if not value:
			raise ValueError("Commit SHA is required for 'commit' mode")
		commits = get_commits_since_commit(value, cwd=cwd)
		progress(f"Found {len(commits)} commits since commit '{value[:7]}'")

	else:
		raise ValueError(f"Unknown mode: {mode}. Valid modes are: tag, date, commit")

	# Set up URL formatters if remote is specified
	url_formatter: Callable[[str], str] | None = None
	compare_url_formatter: Callable[[str, str], str] | None = None

	if remote:
		remotes: dict[str, str] = get_remotes(cwd=cwd)
		if remote not in remotes:
			available = ", ".join(remotes.keys()) if remotes else "none"
			warning(f"Remote '{remote}' not found. Available remotes: {available}")
		else:
			formatters = create_url_formatter(remotes[remote])
			if formatters:
				url_formatter, compare_url_formatter = formatters
				info(f"Using remote '{remote}' for commit URLs")
			else:
				warning(f"Could not parse remote URL: {remotes[remote]}")

	# Generate the changelog
	return format_changelog(
		commits=commits,
		url_formatter=url_formatter,
		latest_tag_version=latest_tag_version,
		current_version=None,  # We don't have a "current version" in local mode
		compare_url_formatter=compare_url_formatter,
	)


@handle_error(message="Error while generating changelog")
def changelog_cli() -> None:
	""" CLI interface for generating changelogs from local git history.

	Usage:
		stouputils changelog [tag|date|commit] [value] [--remote <remote>] [-o <file>]

	Examples:
		stouputils changelog                          # Uses latest tag (default)
		stouputils changelog tag v1.9.0               # All commits since tag v1.9.0
		stouputils changelog date 2026/01/05          # All commits since date
		stouputils changelog commit 847b27e           # All commits since commit
		stouputils changelog --remote origin          # Use origin remote for commit URLs
		stouputils changelog -o CHANGELOG.md          # Output to file
	"""
	parser = argparse.ArgumentParser(
		prog="stouputils changelog",
		description="Generate changelog from local git history",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
Examples:
  stouputils changelog                          Uses latest tag (default)
  stouputils changelog tag v1.9.0               All commits since tag v1.9.0
  stouputils changelog date 2026/01/05          All commits since date
  stouputils changelog commit 847b27e           All commits since commit
  stouputils changelog --remote origin          Use origin remote for commit URLs
  stouputils changelog -o CHANGELOG.md          Output to file
""",
	)

	parser.add_argument("mode",
		nargs="?",
		choices=["tag", "date", "commit"],
		default="tag",
		help="Mode for selecting commits (default: tag)",
	)
	parser.add_argument("value",
		nargs="?",
		help="Value for the mode (tag name, date, or commit SHA). If not provided with 'tag' mode, uses latest tag.",
	)
	parser.add_argument("--remote", "-r",
		help="Remote name to use for commit URLs (e.g., 'origin', 'private'). If not specified, commits show only short SHA.",
	)
	parser.add_argument("--output", "-o",
		help="Output file path. If not specified, prints to stdout.",
	)

	args = parser.parse_args()

	# Generate the changelog
	changelog = generate_local_changelog(
		mode=args.mode,
		value=args.value,
		remote=args.remote,
	)

	# Output the changelog
	if args.output:
		with super_open(args.output, "w") as f:
			f.write(changelog)
		info(f"Changelog written to '{args.output}'")
	else:
		print(changelog)

