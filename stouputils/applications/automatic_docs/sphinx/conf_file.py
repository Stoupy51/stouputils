""" Generation of the ``docs/source/conf.py`` file Sphinx reads.

The file is produced as text rather than imported from a template, because a fair part of it is decided by the caller's arguments:
which forge hosts the sources, which theme renders them, and which pygments styles colour them.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ....lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

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
		value: Mapping to render
	Returns:
		The literal, with JSON booleans translated back to Python ones
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
	version_switcher_url: str = "",
	skip_undocumented: bool = True,
	repo_url: str = "",
	repo_provider: str = "github",
	repo_branch: str = "main",
	source_prefix: str = "",
	edit_link_path: str = "",
	pygments_light_style: str = DEFAULT_LIGHT_STYLE,
	pygments_dark_style: str = DEFAULT_DARK_STYLE,
	default_mode: str = "dark",
	autodoc_mock_imports: list[str] | None = None,
	external_links: list[str] | None = None,
) -> str:
	""" Get the content of the Sphinx configuration file.

	Args:
		project:              Name of the project
		project_dir:          Path to the project directory
		author:               Author of the project
		current_version:      Current version
		copyright:            Copyright information
		html_logo:            URL to the logo
		html_favicon:         URL to the favicon
		html_theme:           Theme rendering the documentation. Defaults to "breeze"
		github_user:          GitHub username
		github_repo:          GitHub repository name
		version_switcher_url: Absolute URL of the ``switcher.json`` listing every published version, empty for no switcher
		skip_undocumented:    Whether to skip undocumented members. Defaults to True
		repo_url:             Repository URL used for source links, ex: "https://gitlab.example.com/group/project"
		repo_provider:        Which key of :data:`.FORGES` describes the repository URL. Defaults to "github"
		repo_branch:          Branch the source links point at. Defaults to "main"
		source_prefix:        Path from the repository root to the importable package's parent, ex: "src/"
		edit_link_path:       Where the Sphinx sources are tracked, enabling the "edit this page" link
			Leave it empty when those sources are generated, since editing them would be pointless.
		pygments_light_style: Pygments style used in light mode
		pygments_dark_style:  Pygments style used in dark mode
		default_mode:         Colour mode a first-time visitor gets: "auto", "light" or "dark"
		autodoc_mock_imports: Packages autodoc replaces with a stub instead of importing
			Only name packages the documented code never calls at import time, since a mock answers every attribute with another mock,
			which turns an ordinary decorator or metaclass into a failed import.
		external_links:       URLs shown as icons in the header before the repository one, ex: a Discord invite or a PyPI page
	Returns:
		Content of the Sphinx configuration file
	"""
	source_url: str = get_source_url(repo_url, repo_provider, repo_branch)
	mocked: list[str] = autodoc_mock_imports if autodoc_mock_imports is not None else []
	parent_of_project_dir: str = clean_path(os.path.dirname(project_dir))
	links: list[str] = [*(external_links or []), *([repo_url] if repo_url else [])]
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
html_theme_options: dict[str, Any] = {python_literal(get_theme_options(html_theme, default_mode, links))}
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

	if version_switcher_url:
		html_context.update({
			"version_id": current_version,
			"version_switcher_url": version_switcher_url,
		})

	conf_content += f"""
html_context = {python_literal(html_context)}

# Autodoc settings
autodoc_default_options: dict[str, bool | str] = {{
	"members": True,
	"member-order": "bysource",
	"special-members": False,
	"undoc-members": False,
	"private-members": False,
	"show-inheritance": True,
	"ignore-module-all": True,
	"exclude-members": "__weakref__",
}}
autodoc_use_legacy_class_based = True

# Tell autodoc to prefer source code over installed package
autodoc_mock_imports = {mocked}
always_document_param_types = True
add_module_names = False

# Docstrings follow the Google style, and a NumPy pass first would undo what keep_attribute_docstring_whole prepares
napoleon_numpy_docstring = False

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
	from stouputils.applications.automatic_docs.sphinx.module_pages import drop_overloads, exact_builtin_references
	register()
	drop_overloads()
	app.connect("doctree-read", exact_builtin_references)
	connect_docstring_fixes(app)

	# Docutils turns the tabs of docstrings and .rst files into 8 spaces before any CSS tab-size can apply
	app.connect("builder-inited", lambda app: app.env.settings.update(tab_width=4))
"""
	if skip_undocumented:
		conf_content += """	app.connect("autodoc-skip-member", skip_undocumented)
"""
	return conf_content

