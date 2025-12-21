""" Sphinx documentation generation utilities.

This module provides a comprehensive set of utilities for automatically generating
and managing Sphinx documentation for Python projects. It handles the creation
of configuration files, index pages, version management, and HTML generation.

Example of usage:

.. code-block:: python

    import stouputils as stp
    from stouputils.applications import automatic_docs

    if __name__ == "__main__":
        automatic_docs.update_documentation(
            root_path=stp.get_root_path(__file__, go_up=1),
            project="stouputils",
            author="Stoupy",
            copyright="2025, Stoupy",
            html_logo="https://avatars.githubusercontent.com/u/35665974",
            html_favicon="https://avatars.githubusercontent.com/u/35665974",
			html_theme="breeze",	# Available themes: breeze, furo, pydata_sphinx_theme, sphinx_rtd_theme, or other you installed
            github_user="Stoupy51",
            github_repo="stouputils",
            version="1.2.0",
            skip_undocumented=True,
        )

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/applications/automatic_docs.gif
  :alt: stouputils automatic_docs examples

Example of GitHub Actions workflow:

.. code-block:: yaml

  name: documentation

  on:
    push:
      tags:
        - 'v*'
    workflow_dispatch:

  permissions:
    contents: write

  jobs:
    docs:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
        - name: Install dependencies
          run: |
            pip install stouputils[docs,data_science]
        - name: Build version docs
          run: |
            python scripts/create_docs.py ${GITHUB_REF#refs/tags/v}
        - name: Deploy to GitHub Pages
          uses: peaceiris/actions-gh-pages@v3
          with:
            publish_branch: gh-pages
            github_token: ${{ secrets.GITHUB_TOKEN }}
            publish_dir: docs/build/html
            keep_files: true
            force_orphan: false
"""
# Imports
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from typing import Any

from ..continuous_delivery import version_to_float
from ..decorators import LogLevels, handle_error, simple_cache
from ..io import clean_path, json_dump, super_open
from ..print import info

# Constants
REQUIREMENTS: list[str] = ["m2r2", "myst_parser"]
""" List of requirements for automatic_docs to work. """

# Functions
def check_dependencies(html_theme: str) -> None:
	""" Check for each requirement if it is installed.

	Args:
		html_theme (str): HTML theme to use for the documentation, to check if it is installed (e.g. "breeze", "pydata_sphinx_theme", "furo", etc.)
	"""
	import importlib
	for requirement in REQUIREMENTS:
		try:
			importlib.import_module(requirement)
		except ImportError as e:
			requirements_str: str = " ".join(REQUIREMENTS)
			raise ImportError(f"{requirement} is not installed. Please install it the following requirements to use automatic_docs: '{requirements_str}'") from e

	if html_theme == "breeze":
		html_theme = "sphinx_breeze_theme"
	try:
		importlib.import_module(html_theme)
	except ImportError as e:
		raise ImportError(f"{html_theme} is not installed. Please add it to your dependencies.") from e

def get_sphinx_conf_content(
	project: str,
	project_dir: str,
	author: str,
	current_version: str,
	copyright: str,
	html_logo: str,
	html_favicon: str,
	html_theme: str = "breeze",
	github_user: str = "",
	github_repo: str = "",
	version_list: list[str] | None = None,
	skip_undocumented: bool = True,
) -> str:
	""" Get the content of the Sphinx configuration file.

	Args:
		project           (str):              Name of the project
		project_dir       (str):              Path to the project directory
		author            (str):              Author of the project
		current_version   (str):              Current version
		copyright         (str):              Copyright information
		html_logo         (str):              URL to the logo
		html_favicon      (str):              URL to the favicon
		github_user       (str):              GitHub username
		github_repo       (str):              GitHub repository name
		version_list      (list[str] | None): List of versions. Defaults to None
		skip_undocumented (bool):             Whether to skip undocumented members. Defaults to True

	Returns:
		str: Content of the Sphinx configuration file
	"""
	parent_of_project_dir: str = clean_path(os.path.dirname(project_dir))
	conf_content: str = f"""
# Imports
import sys
from typing import Any

# Add project_dir directory to Python path for module discovery
sys.path.insert(0, "{parent_of_project_dir}")

# Project information
project: str = "{project}"
copyright: str = "{copyright}"
author: str = "{author}"
release: str = "{current_version}"

# General configuration
extensions: list[str] = [
	# Sphinx's own extensions
	"sphinx.ext.githubpages",
	"sphinx.ext.autodoc",
	"sphinx.ext.napoleon",
	"sphinx.ext.extlinks",
	"sphinx.ext.intersphinx",
	"sphinx.ext.mathjax",
	"sphinx.ext.todo",
	"sphinx.ext.viewcode",

	# External stuff
	"myst_parser",
	"sphinx_copybutton",
	"sphinx_design",
	"sphinx_treeview",
]

myst_enable_extensions = [
	"colon_fence",
	"deflist",
	"fieldlist",
	"substitution",
]
myst_heading_anchors = 3
todo_include_todos = True

copybutton_exclude = ".linenos, .gp"
copybutton_selector = ":not(.prompt) > div.highlight pre"

templates_path: list[str] = ["_templates"]
exclude_patterns: list[str] = []

# HTML output options
html_theme: str = "{html_theme}"
html_static_path: list[str] = ["_static"]
html_css_files: list[str] = ["custom.css"]
html_logo: str = "{html_logo}"
html_title: str = "{project}"
html_favicon: str = "{html_favicon}"

# Theme options
html_theme_options: dict[str, Any] = {{
	"navigation_with_keys": True,
}}
"""
	# Create base html_context dictionary
	html_context: dict[str, Any] = {
		"display_github": True,
		"github_user": github_user,
		"github_repo": github_repo,
		"github_version": "main",
		"conf_py_path": "/docs/source/",
		"source_suffix": [".rst", ".md"],
		"default_mode": "dark",
	}

	# Add version selector if versions are provided
	if version_list and current_version:
		html_context.update({
			"versions": version_list,
			"current_version": current_version,
		})
	html_context_str: str = json_dump(html_context, max_level=1).replace("true", "True").replace("false", "False")

	conf_content += f"""
html_context = {html_context_str}

# Autodoc settings
autodoc_default_options: dict[str, bool | str] = {{
	"members": True,
	"member-order": "bysource",
	"special-members": False,
	"undoc-members": False,
	"private-members": True,
	"show-inheritance": True,
	"ignore-module-all": True,
	"exclude-members": "__weakref__",
}}

# Tell autodoc to prefer source code over installed package
autodoc_mock_imports = []
always_document_param_types = True
add_module_names = False

# Prevent social media cards and images from being used
html_meta = globals().get("html_meta", {{}})
html_meta.pop("image", None)
html_context = globals().get("html_context", {{}})
html_context.pop("image", None)
html_context.pop("social_card", None)
ogp_social_cards = {{"enable": False}}
ogp_site_url = ""
"""

	if skip_undocumented:
		conf_content += """
# Only document items with docstrings
def skip_undocumented(app: Any, what: str, name: str, obj: Any, skip: bool, *args: Any, **kwargs: Any) -> bool:
	if not obj.__doc__:
		return True
	return skip

def setup(app: Any) -> None:
	app.connect("autodoc-skip-member", skip_undocumented)
"""
	return conf_content

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

			# Group versions by major.minor
			from collections import defaultdict
			minor_versions: dict[str, list[str]] = defaultdict(list)
			for version in all_versions:
				parts = version.split(".")
				if len(parts) >= 2:
					minor_key = f"{parts[0]}.{parts[1]}"
					minor_versions[minor_key].append(version)

			# Get the sorted minor version keys
			sorted_minors = sorted(minor_versions.keys(), key=version_to_float, reverse=True)

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

def markdown_to_rst(markdown_content: str) -> str:
	""" Convert markdown content to RST format.

	Args:
		markdown_content (str): Markdown content

	Returns:
		str: RST content
	"""
	if not markdown_content:
		return ""

	# Convert markdown to RST and return it
	import m2r2  # type: ignore
	return m2r2.convert(markdown_content)	# type: ignore

def generate_index_rst(
	readme_path: str,
	index_path: str,
	project: str,
	github_user: str,
	github_repo: str,
	get_versions_function: Callable[[str, str, int], list[str]] = get_versions_from_github,
	recent_minor_versions: int = 2,
) -> None:
	""" Generate index.rst from README.md content.

	Args:
		readme_path            (str): Path to the README.md file
		index_path             (str): Path where index.rst should be created
		project                (str): Name of the project
		github_user            (str): GitHub username
		github_repo            (str): GitHub repository name
		get_versions_function  (Callable[[str, str, int], list[str]]): Function to get versions from GitHub
		recent_minor_versions  (int): Number of recent minor versions to show all patches for. Defaults to 2
	"""
	# Read README content
	with open(readme_path, encoding="utf-8") as f:
		readme_content: str = f.read()

	# Generate version selector
	version_selector: str = "\n\n**Versions**: "

	# Get versions from GitHub
	version_list: list[str] = get_versions_function(github_user, github_repo, recent_minor_versions)

	# Create version links
	version_links: list[str] = []
	for version in version_list:
		if version == "latest":
			version_links.append("`latest <../latest/>`_")
		else:
			version_links.append(f"`v{version} <../v{version}/>`_")
	version_selector += ", ".join(version_links)

	# Generate module documentation section
	project_module: str = project.lower()
	module_docs: str = f"""
.. toctree::
   :maxdepth: 10

   modules/{project_module}
"""
	module_docs = markdown_to_rst(f"""
Here is the complete unsorted documentation for all modules in the {project} project.<br>
Prefer to use the search button at the top to find what you need!
""") + module_docs

	# Convert markdown to RST
	rst_content: str = f"""
✨ Welcome to {project.capitalize()} Documentation ✨
{'=' * 100}
{version_selector}

{markdown_to_rst(readme_content)}

📖 Module Documentation
{'-' * 100}
{module_docs}
"""

	# Write the RST file
	with open(index_path, "w", encoding="utf-8") as f:
		f.write(rst_content)

def generate_documentation(
	source_dir: str,
	modules_dir: str,
	project_dir: str,
	build_dir: str,
) -> None:
	""" Generate documentation using Sphinx.

	Args:
		source_dir        (str): Source directory
		modules_dir       (str): Modules directory
		project_dir       (str): Project directory
		build_dir         (str): Build directory
	"""
	# Generate module documentation using sphinx-apidoc
	subprocess.run([
		sys.executable,
		"-m", "sphinx.ext.apidoc",
		"-o", modules_dir,
		"-f", "-e", "-M",
		"--no-toc",
		"-P",
		"--implicit-namespaces",
		"--module-first",
		project_dir,
	], check=True)

	# Build HTML documentation
	subprocess.run([
		sys.executable,
		"-m", "sphinx",
		"-b", "html",
		"-a",
		source_dir,
		build_dir,
	], check=True)

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
def update_documentation(
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
	version: str | None = None,
	skip_undocumented: bool = True,
	recent_minor_versions: int = 2,

	get_versions_function: Callable[[str, str, int], list[str]] = get_versions_from_github,
	generate_index_function: Callable[..., None] = generate_index_rst,
	generate_docs_function: Callable[..., None] = generate_documentation,
	generate_redirect_function: Callable[[str], None] = generate_redirect_html,
	get_conf_content_function: Callable[..., str] = get_sphinx_conf_content
) -> None:
	""" Update the Sphinx documentation.

	Args:
		root_path                  (str): Root path of the project
		project                    (str): Name of the project
		project_dir                (str): Path to the project directory (to be used with generate_docs_function)
		author                     (str): Author of the project
		copyright                  (str): Copyright information
		html_logo                  (str): URL to the logo
		html_favicon               (str): URL to the favicon
		html_theme                 (str): Theme to use for the documentation. Defaults to "breeze"
		github_user                (str): GitHub username
		github_repo                (str): GitHub repository name
		version                    (str | None): Version to build documentation for (e.g. "1.0.0", defaults to "latest")
		skip_undocumented          (bool): Whether to skip undocumented members. Defaults to True
		recent_minor_versions      (int): Number of recent minor versions to show all patches for. Defaults to 2

		get_versions_function      (Callable[[str, str, int], list[str]]): Function to get versions from GitHub
		generate_index_function    (Callable[..., None]): Function to generate index.rst
		generate_docs_function     (Callable[..., None]): Function to generate documentation
		generate_redirect_function (Callable[[str], None]): Function to create redirect file
		get_conf_content_function  (Callable[..., str]): Function to get Sphinx conf.py content
	"""
	check_dependencies(html_theme)

	# Setup paths
	root_path = clean_path(root_path)
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

	# Create custom CSS file to reduce heading sizes
	custom_css_path: str = f"{static_dir}/custom.css"
	with super_open(custom_css_path, "w") as f:
		f.write("""
/* Custom CSS for Sphinx documentation */
/* Reduce heading sizes */
h1 { font-size: 2.0em !important; }
h2 { font-size: 1.6em !important; }
h3 { font-size: 1.4em !important; }
h4 { font-size: 1.2em !important; }
h5 { font-size: 1.0em !important; }
h6 { font-size: 0.9em !important; }

/* Gradient animation keyframes */
@keyframes shine-slide {
	0% { background-position: -200% center; }
	100% { background-position: 200% center; }
}

/* On hover animation for various elements */
a, h1, h2, h3, h4, h5, h6, .admonition {
	transition: transform 0.3s;
	position: relative;
}

a:hover, h1:hover, h2:hover, h3:hover, h4:hover, h5:hover, h6:hover, .admonition:hover {
	transform: scale(1.05);
}
a:hover {
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
	animation: shine-slide 2s linear infinite;
}
""")

	# Generate index.rst from README.md
	readme_path: str = f"{root_path}/README.md"
	index_path: str = f"{source_dir}/index.rst"
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

