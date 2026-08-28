""" Orchestration of a documentation build: lay out the folders, write the generated files, then run Sphinx.

``sphinx_docs`` is the only entry point most projects ever call.
Every step it performs is a parameter, so a project needing a different landing page or a different build command
replaces that one callable instead of forking the whole routine.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ....lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import os
import shutil
from collections.abc import Callable

from ....decorators import LogLevels, handle_error
from ....io.path import clean_path
from ....print.message import info
from ..common import generate_redirect_html, get_versions_from_github
from .conf_file import get_sphinx_conf_content
from .index_page import generate_index_md
from .theming import DEFAULT_DARK_STYLE, DEFAULT_LIGHT_STYLE, check_dependencies, write_custom_css


# Functions
def generate_documentation(
	source_dir: str,
	modules_dir: str,
	project_dir: str,
	build_dir: str,
) -> None:
	""" Generate documentation using Sphinx.

	Args:
		source_dir:  Source directory
		modules_dir: Modules directory
		project_dir: Project directory
		build_dir:   Build directory
	"""
	# Generate module documentation using sphinx-apidoc
	from sphinx.ext.apidoc import main as sphinx_apidoc_main
	sphinx_apidoc_main([
		"-o", modules_dir,
		"-f", "-e", "-M",
		"--no-toc",
		"-P",
		"--implicit-namespaces",
		"--module-first",
		project_dir,
	])

	# Build HTML documentation
	from sphinx.cmd.build import main as sphinx_build_main
	sphinx_build_main([
		"-b", "html",
		"-a",
		"-v",
		source_dir,
		build_dir,
	])


@handle_error(error_log=LogLevels.WARNING_TRACEBACK)
def sphinx_docs(
	root_path: str,
	project: str,
	project_dir: str = "",
	author: str = "Author",
	copyright: str = "2025, Author",
	html_logo: str = "",
	html_favicon: str = "",
	html_theme: str = "breeze",
	github_user: str = "",
	github_repo: str = "",
	repo_url: str = "",
	repo_provider: str = "github",
	repo_branch: str = "main",
	edit_link_path: str = "",
	pygments_light_style: str = DEFAULT_LIGHT_STYLE,
	pygments_dark_style: str = DEFAULT_DARK_STYLE,
	default_mode: str = "dark",
	autodoc_mock_imports: list[str] | None = None,
	version: str | None = None,
	skip_undocumented: bool = True,
	recent_minor_versions: int = 2,

	get_versions_function: Callable[[str, str, int], list[str]] = get_versions_from_github,
	generate_index_function: Callable[..., None] = generate_index_md,
	generate_docs_function: Callable[..., None] = generate_documentation,
	generate_redirect_function: Callable[[str], None] = generate_redirect_html,
	get_conf_content_function: Callable[..., str] = get_sphinx_conf_content
) -> None:
	""" Update the Sphinx documentation.

	Args:
		root_path:             Root path of the project
		project:               Name of the project
		project_dir:           Path to the project directory (to be used with generate_docs_function)
		author:                Author of the project
		copyright:             Copyright information
		html_logo:             URL to the logo
		html_favicon:          URL to the favicon
		html_theme:            Theme to use for the documentation. Defaults to "breeze"
		github_user:           GitHub username
		github_repo:           GitHub repository name
		repo_url:              Repository URL used for source links, defaulting to the GitHub one built from the two above
		repo_provider:         Which key of :data:`.FORGES` describes the repository URL. Defaults to "github"
		repo_branch:           Branch the source links point at. Defaults to "main"
		edit_link_path:        Where the Sphinx sources are tracked, enabling the "edit this page" link, ex: "docs/source"
		pygments_light_style:  Pygments style used in light mode
		pygments_dark_style:   Pygments style used in dark mode
		default_mode:          Colour mode a first-time visitor gets: "auto", "light" or "dark"
		autodoc_mock_imports:  Packages autodoc stubs out instead of importing, defaulting to none
		version:               Version to build documentation for (e.g. "1.0.0", defaults to "latest")
		skip_undocumented:     Whether to skip undocumented members. Defaults to True
		recent_minor_versions: Number of recent minor versions to show all patches for. Defaults to 2

		get_versions_function:      Function to get versions from GitHub
		generate_index_function:    Function to generate index.md
		generate_docs_function:     Function to generate documentation
		generate_redirect_function: Function to create redirect file
		get_conf_content_function:  Function to get Sphinx conf.py content
	"""
	check_dependencies(html_theme)

	# Setup paths
	root_path = clean_path(root_path)

	# A src/ layout puts the package one folder below the repository root, and source links must say so
	package_parent: str = clean_path(os.path.dirname(project_dir)) if project_dir else root_path
	relative_parent: str = package_parent.removeprefix(root_path).strip("/")
	source_prefix: str = f"{relative_parent}/" if relative_parent else ""
	if not repo_url and github_user and github_repo:
		repo_url = f"https://github.com/{github_user}/{github_repo}"

	docs_dir: str = f"{root_path}/docs"
	source_dir: str = f"{docs_dir}/source"
	modules_dir: str = f"{source_dir}/modules"
	static_dir: str = f"{source_dir}/_static"
	templates_dir: str = f"{source_dir}/_templates"
	html_dir: str = f"{docs_dir}/build/html"

	# Remove "v" from version if it is a string (just in case)
	version = version.replace("v", "") if isinstance(version, str) else version

	# Modify build directory if version is specified
	latest_dir: str = f"{html_dir}/latest"
	build_dir: str = latest_dir if not version else f"{html_dir}/v{version}"

	# Create directories if they don't exist
	for dir in [modules_dir, static_dir, templates_dir]:
		os.makedirs(dir, exist_ok=True)

	write_custom_css(static_dir)

	# Generate index.md from README.md (use MyST instead of converting to RST)
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

	# Clean up old module documentation
	if os.path.exists(modules_dir):
		shutil.rmtree(modules_dir)
	os.makedirs(modules_dir, exist_ok=True)

	# Get versions and current version for conf.py
	version_list: list[str] = get_versions_function(github_user, github_repo, recent_minor_versions)
	current_version: str = version if version else "latest"

	# Generate conf.py
	conf_path: str = f"{source_dir}/conf.py"
	conf_content: str = get_conf_content_function(
		project=project,
		project_dir=project_dir,
		author=author,
		current_version=current_version,
		copyright=copyright,
		html_logo=html_logo,
		html_favicon=html_favicon,
		html_theme=html_theme,
		github_user=github_user,
		github_repo=github_repo,
		version_list=version_list,
		skip_undocumented=skip_undocumented,
		repo_url=repo_url,
		repo_provider=repo_provider,
		repo_branch=repo_branch,
		source_prefix=source_prefix,
		edit_link_path=edit_link_path,
		pygments_light_style=pygments_light_style,
		pygments_dark_style=pygments_dark_style,
		default_mode=default_mode,
		autodoc_mock_imports=autodoc_mock_imports,
	)
	with open(conf_path, "w", encoding="utf-8") as f:
		f.write(conf_content)

	# Generate documentation
	generate_docs_function(
		source_dir=source_dir,
		modules_dir=modules_dir,
		project_dir=project_dir if project_dir else f"{root_path}/{project}",
		build_dir=build_dir,
	)

	# Add index.html to the build directory that redirects to the latest version
	generate_redirect_function(f"{html_dir}/index.html")

	# If version is specified, copy the build directory to latest too
	# This is useful for GitHub Actions to prevent re-building the documentation from scratch without the version
	if version:
		if os.path.exists(latest_dir):
			shutil.rmtree(latest_dir)
		shutil.copytree(build_dir, latest_dir, dirs_exist_ok=True)

	info("Documentation updated successfully!")
	info(f"You can view the documentation by opening {build_dir}/index.html")

