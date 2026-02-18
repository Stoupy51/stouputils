""" Zensical documentation generation utilities.

This module provides a comprehensive set of utilities for automatically generating
and managing documentation for Python projects using **Zensical** (a modern static
site generator based on MkDocs Material) and **mkdocstrings** for API reference
generation from docstrings.

It handles the creation of configuration files, index pages, API reference pages,
version management, and HTML generation.

Example of usage:

.. code-block:: python

    import stouputils as stp
    from stouputils.applications import automatic_docs

    if __name__ == "__main__":
        automatic_docs.zensical_docs(
            root_path=stp.get_root_path(__file__, go_up=1),
            project="stouputils",
            author="Stoupy",
            copyright="2025, Stoupy",
            html_logo="https://avatars.githubusercontent.com/u/35665974",
            html_favicon="https://avatars.githubusercontent.com/u/35665974",
            github_user="Stoupy51",
            github_repo="stouputils",
            version="1.2.0",
            skip_undocumented=True,
        )
"""
# Imports
import os
import shutil
import subprocess
import sys
from collections.abc import Callable

from ...config import StouputilsConfig as Cfg
from ...continuous_delivery import version_to_float
from ...decorators import LogLevels, handle_error, simple_cache
from ...io.path import clean_path, super_open
from ...print.message import info


# Functions
def check_dependencies() -> None:
	""" Check for each requirement if it is installed. """
	import importlib
	for requirement in Cfg.AUTO_DOCS_REQUIREMENTS:
		try:
			importlib.import_module(requirement)
		except ImportError as e:
			requirements_str: str = " ".join(Cfg.AUTO_DOCS_REQUIREMENTS)
			raise ImportError(f"{requirement} is not installed. Please install the following requirements to use automatic_docs: '{requirements_str}'") from e

def _download_asset(url: str, target_path: str) -> None:
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

def get_zensical_config_content(
	project: str,
	project_dir: str,
	docs_dir: str,
	site_dir: str,
	author: str,
	current_version: str,
	copyright: str,
	html_logo: str,
	html_favicon: str,
	github_user: str = "",
	github_repo: str = "",
	version_list: list[str] | None = None,
	skip_undocumented: bool = True,
	api_pages: list[tuple[str, str]] | None = None,
) -> str:
	""" Get the content of the Zensical configuration file (zensical.toml).

	Args:
		project           (str):              Name of the project
		project_dir       (str):              Path to the project directory
		docs_dir          (str):              Path to the docs source directory (relative to root)
		site_dir          (str):              Path to the build output directory (relative to root)
		author            (str):              Author of the project
		current_version   (str):              Current version
		copyright         (str):              Copyright information
		html_logo         (str):              Path to the logo image (relative to docs_dir)
		html_favicon      (str):              Path to the favicon image (relative to docs_dir)
		github_user       (str):              GitHub username
		github_repo       (str):              GitHub repository name
		version_list      (list[str] | None): List of versions. Defaults to None
		skip_undocumented (bool):             Whether to skip undocumented members. Defaults to True
		api_pages         (list[tuple[str, str]] | None): List of (module_name, md_filename) tuples for nav

	Returns:
		str: Content of the Zensical configuration file (TOML)
	"""
	parent_of_project_dir: str = clean_path(os.path.dirname(project_dir))

	# Build repo URL
	repo_url: str = f"https://github.com/{github_user}/{github_repo}" if github_user and github_repo else ""
	repo_name: str = f"{github_user}/{github_repo}" if github_user and github_repo else ""

	# Project section
	config: str = f"""[project]
site_name = "{project}"
site_description = "{project} documentation — v{current_version}"
site_author = "{author}"
copyright = "Copyright &copy; {copyright}"
docs_dir = "{docs_dir}"
site_dir = "{site_dir}"
"""
	if repo_url:
		config += f'repo_url = "{repo_url}"\n'
		config += f'repo_name = "{repo_name}"\n'

	config += 'extra_css = ["_static/custom.css"]\n'

	# Navigation
	if api_pages:
		nav_items: list[str] = []
		for module_name, md_filename in api_pages:
			nav_items.append(f'        {{ "{module_name}" = "api/{md_filename}" }}')
		api_nav: str = ",\n".join(nav_items)
		config += f"""
nav = [
    {{ "Home" = "index.md" }},
    {{ "API Reference" = [
{api_nav},
    ] }},
]
"""

	# Theme section
	config += """
[project.theme]
language = "en"
"""
	if html_favicon:
		config += f'favicon = "{html_favicon}"\n'
	if html_logo:
		config += f'logo = "{html_logo}"\n'

	config += """
features = [
    "content.code.copy",
    "content.code.annotate",
    "content.code.select",
    "content.tooltips",
    "navigation.footer",
    "navigation.instant",
    "navigation.instant.prefetch",
    "navigation.sections",
    "navigation.top",
    "navigation.path",
    "navigation.indexes",
    "search.highlight",
]

[[project.theme.palette]]
scheme = "slate"
toggle.icon = "lucide/sun"
toggle.name = "Switch to light mode"

[[project.theme.palette]]
scheme = "default"
toggle.icon = "lucide/moon"
toggle.name = "Switch to dark mode"
"""

	# mkdocstrings plugin configuration
	show_if_no_docstring: str = "false" if skip_undocumented else "true"
	config += f"""
[project.plugins.mkdocstrings.handlers.python]
paths = ["{parent_of_project_dir}"]

[project.plugins.mkdocstrings.handlers.python.options]
docstring_style = "google"
show_source = true
members_order = "source"
show_root_heading = true
show_symbol_type_heading = true
show_symbol_type_toc = true
show_if_no_docstring = {show_if_no_docstring}
inherited_members = true
merge_init_into_class = true
group_by_category = true
"""
	return config

@simple_cache()
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
			from collections import defaultdict
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

def generate_index_md(
	readme_path: str,
	index_path: str,
	project: str,
	github_user: str,
	github_repo: str,
	get_versions_function: Callable[[str, str, int], list[str]] = get_versions_from_github,
	recent_minor_versions: int = 2,
) -> None:
	""" Generate ``index.md`` from README.md content.

	This keeps the README content as Markdown and creates the home page for the
	Zensical documentation. Navigation to API docs is handled by the Zensical
	config (nav or auto-discovery).

	Args:
		readme_path            (str): Path to the README.md file
		index_path             (str): Path where index.md should be created
		project                (str): Name of the project
		github_user            (str): GitHub username
		github_repo            (str): GitHub repository name
		get_versions_function  (Callable[[str, str, int], list[str]]): Function to get versions from GitHub
		recent_minor_versions  (int): Number of recent minor versions to show all patches for. Defaults to 2
	"""
	# Read README content
	with open(readme_path, encoding="utf-8") as f:
		readme_content: str = f.read()

	# Generate version selector (markdown links)
	version_list: list[str] = get_versions_function(github_user, github_repo, recent_minor_versions)
	version_links: list[str] = []
	for version in version_list:
		if version == "latest":
			version_links.append('<a href="../latest/">latest</a>')
		else:
			version_links.append(f'<a href="../v{version}/">v{version}</a>')
	version_selector: str = "\n\n**Versions**: " + ", ".join(version_links)

	# Build final markdown content
	md_content: str = f"""# Welcome to {project.capitalize()} Documentation

{version_selector}

{readme_content}
"""

	# Write the Markdown file
	with open(index_path, "w", encoding="utf-8") as f:
		f.write(md_content)

def generate_api_pages(
	api_dir: str,
	project: str,
	project_dir: str,
) -> list[tuple[str, str]]:
	""" Walk the project directory and generate Markdown pages with ``:::`` directives
	for mkdocstrings API documentation.

	Args:
		api_dir      (str): Directory where API markdown pages should be written
		project      (str): Name of the project (package name)
		project_dir  (str): Path to the project directory (Python package root)

	Returns:
		list[tuple[str, str]]: List of (module_name, md_filename) tuples
	"""
	pages: list[tuple[str, str]] = []
	project_dir = clean_path(project_dir)
	parent_dir: str = os.path.dirname(project_dir)
	os.makedirs(api_dir, exist_ok=True)

	for root, dirs, files in os.walk(project_dir):
		# Skip __pycache__ and sort directories for consistent ordering
		dirs[:] = sorted(d for d in dirs if d != "__pycache__")

		# Compute the Python module name from path
		rel_path: str = os.path.relpath(root, parent_dir).replace(os.sep, "/")
		module_name: str = rel_path.replace("/", ".")

		# Only process Python packages (directories with __init__.py)
		if "__init__.py" not in files:
			continue

		# Create page for the package itself
		md_filename: str = f"{module_name}.md"
		md_path: str = f"{api_dir}/{md_filename}"
		with open(md_path, "w", encoding="utf-8") as f:
			f.write(f"# {module_name}\n\n::: {module_name}\n")
		pages.append((module_name, md_filename))

		# Create pages for individual submodules (non-__init__ .py files)
		for fname in sorted(files):
			if fname.endswith(".py") and fname != "__init__.py":
				sub_module: str = fname[:-3]
				full_module: str = f"{module_name}.{sub_module}"
				sub_md_filename: str = f"{full_module}.md"
				sub_md_path: str = f"{api_dir}/{sub_md_filename}"
				with open(sub_md_path, "w", encoding="utf-8") as f:
					f.write(f"# {full_module}\n\n::: {full_module}\n")
				pages.append((full_module, sub_md_filename))

	return pages

def generate_documentation(
	config_path: str,
	root_path: str,
) -> None:
	""" Generate documentation using Zensical.

	Args:
		config_path (str): Path to the zensical.toml configuration file
		root_path   (str): Root path of the project (working directory for the build)
	"""
	# Find the zensical executable
	zensical_cmd: str | None = shutil.which("zensical")
	if not zensical_cmd:
		raise RuntimeError(
			"'zensical' command not found in PATH. "
			"Install it with: pip install zensical"
		)

	# Run zensical build
	info(f"Running: {zensical_cmd} build -f {config_path} --clean")
	result: subprocess.CompletedProcess[bytes] = subprocess.run(
		[zensical_cmd, "build", "-f", config_path, "--clean"],
		cwd=root_path,
		stdout=sys.stdout,
		stderr=sys.stderr,
	)
	if result.returncode != 0:
		raise RuntimeError(f"Zensical build failed (exit code {result.returncode})")

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

@handle_error(error_log=LogLevels.WARNING_TRACEBACK)
def zensical_docs(
	root_path: str,
	project: str,
	project_dir: str = "",
	author: str = "Author",
	copyright: str = "2025, Author",
	html_logo: str = "",
	html_favicon: str = "",
	html_theme: str = "",
	github_user: str = "",
	github_repo: str = "",
	version: str | None = None,
	skip_undocumented: bool = True,
	recent_minor_versions: int = 2,

	get_versions_function: Callable[[str, str, int], list[str]] = get_versions_from_github,
	generate_index_function: Callable[..., None] = generate_index_md,
	generate_api_pages_function: Callable[..., list[tuple[str, str]]] = generate_api_pages,
	generate_docs_function: Callable[..., None] = generate_documentation,
	generate_redirect_function: Callable[[str], None] = generate_redirect_html,
	get_config_content_function: Callable[..., str] = get_zensical_config_content,
) -> None:
	""" Update the documentation using Zensical and mkdocstrings.

	Args:
		root_path                    (str): Root path of the project
		project                      (str): Name of the project
		project_dir                  (str): Path to the project directory (to be used with generate_docs_function)
		author                       (str): Author of the project
		copyright                    (str): Copyright information
		html_logo                    (str): URL or path to the logo image
		html_favicon                 (str): URL or path to the favicon image
		html_theme                   (str): Unused (kept for backward compatibility)
		github_user                  (str): GitHub username
		github_repo                  (str): GitHub repository name
		version                      (str | None): Version to build documentation for (e.g. "1.0.0", defaults to "latest")
		skip_undocumented            (bool): Whether to skip undocumented members. Defaults to True
		recent_minor_versions        (int): Number of recent minor versions to show all patches for. Defaults to 2

		get_versions_function        (Callable[[str, str, int], list[str]]): Function to get versions from GitHub
		generate_index_function      (Callable[..., None]): Function to generate index.md
		generate_api_pages_function  (Callable[..., list[tuple[str, str]]]): Function to generate API pages
		generate_docs_function       (Callable[..., None]): Function to generate documentation
		generate_redirect_function   (Callable[[str], None]): Function to create redirect file
		get_config_content_function  (Callable[..., str]): Function to get Zensical config content
	"""
	_ = html_theme  # Unused (Zensical uses its own built-in theme)
	check_dependencies()

	# Setup paths
	root_path = clean_path(root_path)
	docs_dir: str = f"{root_path}/docs"
	source_dir: str = f"{docs_dir}/source"
	api_dir: str = f"{source_dir}/api"
	static_dir: str = f"{source_dir}/_static"
	html_dir: str = f"{docs_dir}/build/html"

	# Resolve project directory
	effective_project_dir: str = project_dir if project_dir else f"{root_path}/{project}"

	# Remove "v" from version if it is a string (just in case)
	version = version.replace("v", "") if isinstance(version, str) else version

	# Modify build directory if version is specified
	latest_dir: str = f"{html_dir}/latest"
	build_dir: str = latest_dir if not version else f"{html_dir}/v{version}"

	# Create directories
	for d in [api_dir, static_dir]:
		os.makedirs(d, exist_ok=True)

	# Download logo and favicon if they are URLs
	logo_ref: str = html_logo
	favicon_ref: str = html_favicon
	if html_logo and html_logo.startswith("http"):
		local_logo: str = f"{static_dir}/logo.png"
		_download_asset(html_logo, local_logo)
		logo_ref = "_static/logo.png"
	if html_favicon and html_favicon.startswith("http"):
		local_favicon: str = f"{static_dir}/favicon.png"
		_download_asset(html_favicon, local_favicon)
		favicon_ref = "_static/favicon.png"

	# Create custom CSS
	custom_css_path: str = f"{static_dir}/custom.css"
	with super_open(custom_css_path, "w") as f:
		f.write("""
/* Custom CSS for documentation */
/* Gradient animation keyframes */
@keyframes shine-slide {
	0% { background-position: -200% center; }
	100% { background-position: 200% center; }
}

/* On hover animation for links */
a:hover, a:hover span {
	background: linear-gradient(
		110deg,
		currentColor 0%,
		currentColor 40%,
		white 50%,
		currentColor 60%,
		currentColor 100%
	);
	background-size: 200% 100%;
	background-clip: text;
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
	animation: shine-slide 3.5s linear infinite;
}
""")

	# Generate index.md from README.md
	readme_path: str = f"{root_path}/README.md"
	index_path: str = f"{source_dir}/index.md"
	generate_index_function(
		readme_path=readme_path,
		index_path=index_path,
		project=project,
		github_user=github_user,
		github_repo=github_repo,
		get_versions_function=get_versions_function,
		recent_minor_versions=recent_minor_versions,
	)

	# Clean up old API documentation and regenerate
	if os.path.exists(api_dir):
		shutil.rmtree(api_dir)
	os.makedirs(api_dir, exist_ok=True)

	# Generate API pages with ::: directives for mkdocstrings
	api_pages: list[tuple[str, str]] = generate_api_pages_function(
		api_dir=api_dir,
		project=project,
		project_dir=effective_project_dir,
	)
	info(f"Generated {len(api_pages)} API documentation pages")

	# Get versions and current version for config
	version_list: list[str] = get_versions_function(github_user, github_repo, recent_minor_versions)
	current_version: str = version if version else "latest"

	# Generate zensical.toml config
	# Paths in zensical.toml are relative to the config file location (root_path)
	relative_docs_dir: str = os.path.relpath(source_dir, root_path).replace(os.sep, "/")
	relative_site_dir: str = os.path.relpath(build_dir, root_path).replace(os.sep, "/")

	config_content: str = get_config_content_function(
		project=project,
		project_dir=effective_project_dir,
		docs_dir=relative_docs_dir,
		site_dir=relative_site_dir,
		author=author,
		current_version=current_version,
		copyright=copyright,
		html_logo=logo_ref,
		html_favicon=favicon_ref,
		github_user=github_user,
		github_repo=github_repo,
		version_list=version_list,
		skip_undocumented=skip_undocumented,
		api_pages=api_pages,
	)
	config_path: str = f"{root_path}/zensical.toml"
	with open(config_path, "w", encoding="utf-8") as f:
		f.write(config_content)

	# Build documentation with Zensical
	generate_docs_function(
		config_path=config_path,
		root_path=root_path,
	)

	# Add index.html to the build directory that redirects to the latest version
	generate_redirect_function(f"{html_dir}/index.html")

	# If version is specified, copy the build directory to latest too
	if version:
		if os.path.exists(latest_dir):
			shutil.rmtree(latest_dir)
		shutil.copytree(build_dir, latest_dir, dirs_exist_ok=True)

	info("Documentation updated successfully!")
	info(f"You can view the documentation by opening {build_dir}/index.html")

