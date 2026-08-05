""" Generation of the ``docs/source/conf.py`` file Sphinx reads.

The file is produced as text rather than imported from a template, because a fair part of it is decided by the
caller's arguments: which forge hosts the sources, which theme renders them, and which pygments styles colour them.
"""
# Imports
import os
from typing import Any

from ....io.json import json_dump
from ....io.path import clean_path
from .forges import get_edit_url, get_source_url
from .theming import DEFAULT_DARK_STYLE, DEFAULT_LIGHT_STYLE, get_theme_options


# Functions
def python_literal(value: dict[str, Any]) -> str:
	""" Render a mapping as a Python literal fit for the generated ``conf.py``.

	Args:
		value (dict[str, Any]): Mapping to render
	Returns:
		str: The literal, with JSON booleans translated back to Python ones

	Examples:
		>>> python_literal({"a": True, "b": False})
		'{\\n\\t"a": True,\\n\\t"b": False\\n}\\n'
	"""
	return json_dump(value, max_level=1).replace("true", "True").replace("false", "False")


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
	repo_url: str = "",
	repo_provider: str = "github",
	repo_branch: str = "main",
	source_prefix: str = "",
	edit_link_path: str = "",
	pygments_light_style: str = DEFAULT_LIGHT_STYLE,
	pygments_dark_style: str = DEFAULT_DARK_STYLE,
	default_mode: str = "dark",
) -> str:
	""" Get the content of the Sphinx configuration file.

	Args:
		project              (str):              Name of the project
		project_dir          (str):              Path to the project directory
		author               (str):              Author of the project
		current_version      (str):              Current version
		copyright            (str):              Copyright information
		html_logo            (str):              URL to the logo
		html_favicon         (str):              URL to the favicon
		html_theme           (str):              Theme rendering the documentation. Defaults to "breeze"
		github_user          (str):              GitHub username
		github_repo          (str):              GitHub repository name
		version_list         (list[str] | None): List of versions. Defaults to None
		skip_undocumented    (bool):             Whether to skip undocumented members. Defaults to True
		repo_url             (str):              Repository URL used for source links, ex: "https://gitlab.example.com/group/project"
		repo_provider        (str):              Which key of :data:`.FORGES` describes the repository URL. Defaults to "github"
		repo_branch          (str):              Branch the source links point at. Defaults to "main"
		source_prefix        (str):              Path from the repository root to the importable package's parent, ex: "src/"
		edit_link_path       (str):              Where the Sphinx sources are tracked, enabling the "edit this page" link
			Leave it empty when those sources are generated, since editing them would be pointless.
		pygments_light_style (str):              Pygments style used in light mode
		pygments_dark_style  (str):              Pygments style used in dark mode
		default_mode         (str):              Colour mode a first-time visitor gets: "auto", "light" or "dark"

	Returns:
		str: Content of the Sphinx configuration file
	"""
	source_url: str = get_source_url(repo_url, repo_provider, repo_branch)
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
	"sphinx.ext.linkcode",

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

# Linkcode configuration to link to the repository's source code
source_url: str = "{source_url}"
source_prefix: str = "{source_prefix}"

def linkcode_resolve(domain: str, info: dict) -> str | None:
    if domain != "py" or not info["module"] or not source_url:
        return None
    filename = source_prefix + info["module"].replace(".", "/")
    return source_url.format(filename=filename)

# Allow both .rst and .md (MyST) sources
source_suffix = {{
    ".rst": "restructuredtext",
    ".md": "markdown",
}}

# HTML output options
html_theme: str = "{html_theme}"
html_static_path: list[str] = ["_static"]
html_css_files: list[str] = ["custom.css"]
html_logo: str = "{html_logo}"
html_title: str = "{project}"
html_favicon: str = "{html_favicon}"

# Syntax highlighting, one palette per colour mode
# Pygments tags most identifiers as a bare Name, so a style colouring Name repaints whole snippets in one hue
pygments_light_style: str = "{pygments_light_style}"
pygments_dark_style: str = "{pygments_dark_style}"

# Theme options
html_theme_options: dict[str, Any] = {python_literal(get_theme_options(html_theme, default_mode))}
"""
	# An empty github_user still satisfies the theme's "is not None" test, which is how a project hosted
	# elsewhere ends up with every page linking to https://github.com///edit/main/, so only set them when real.
	html_context: dict[str, Any] = {
		"conf_py_path": "/docs/source/",
		"default_mode": default_mode,
	}
	if github_user and github_repo:
		html_context.update({
			"display_github": True,
			"github_user": github_user,
			"github_repo": github_repo,
			"github_version": repo_branch,
		})
	edit_url: str = get_edit_url(repo_url, repo_provider, repo_branch, edit_link_path)
	if edit_url:
		html_context["source_edit_url"] = edit_url

	# Add version selector if versions are provided
	if version_list and current_version:
		html_context.update({
			"versions": version_list,
			"current_version": current_version,
		})

	conf_content += f"""
html_context = {python_literal(html_context)}

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
autodoc_use_legacy_class_based = True

# Tell autodoc to prefer source code over installed package
autodoc_mock_imports = ["mlflow", "polars", "mypy", "uv"]
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
"""

	# Give reStructuredText the blank lines it needs before doctest blocks, then apply the optional skip
	# Highlighting is registered here because it must exist before Sphinx lexes the first code block
	conf_content += """
def setup(app: Any) -> None:
	from stouputils.applications.automatic_docs import connect_docstring_fixes
	from stouputils.applications.automatic_docs.sphinx.highlighting import register
	register()
	connect_docstring_fixes(app)
"""
	if skip_undocumented:
		conf_content += """	app.connect("autodoc-skip-member", skip_undocumented)
"""
	return conf_content

