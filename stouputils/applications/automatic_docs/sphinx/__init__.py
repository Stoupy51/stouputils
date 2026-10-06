""" 📖 Sphinx documentation generation utilities.

This subpackage provides a comprehensive set of utilities for automatically generating
and managing Sphinx documentation for Python projects. It handles the creation of configuration files,
index pages, version management, and HTML generation.

The work is split by concern: :mod:`.forges` knows where source files live on the web,
:mod:`.theming` decides how code is coloured, :mod:`.conf_file` writes the generated ``conf.py``,
:mod:`.index_page` builds the landing page, :mod:`.module_pages` the API reference, and :mod:`.builder` runs the whole thing.

Example of usage:

.. code-block:: python

    import stouputils as stp
    from stouputils.applications import automatic_docs

    if __name__ == "__main__":
        automatic_docs.sphinx_docs(
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
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ....lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .builder import generate_documentation, sphinx_docs, write_version_switcher
from .conf_file import get_sphinx_conf_content, python_literal
from .forges import FORGES, ForgeUrls, get_edit_url, get_source_url
from .highlighting import VSCodeDarkPlusStyle, VSCodeLightPlusStyle, VSCodeSemanticFilter
from .index_page import generate_index_md
from .module_pages import ROOT_TITLE, exported_names, heading, is_public, package_page, titled, write_module_pages
from .theming import (
	CUSTOM_CSS,
	DEFAULT_DARK_STYLE,
	DEFAULT_LIGHT_STYLE,
	SIDEBAR_NAV,
	check_dependencies,
	get_theme_options,
	write_custom_css,
	write_sidebar_nav,
)

__all__ = [
	"CUSTOM_CSS",
	"DEFAULT_DARK_STYLE",
	"DEFAULT_LIGHT_STYLE",
	"FORGES",
	"ROOT_TITLE",
	"SIDEBAR_NAV",
	"ForgeUrls",
	"VSCodeDarkPlusStyle",
	"VSCodeLightPlusStyle",
	"VSCodeSemanticFilter",
	"check_dependencies",
	"exported_names",
	"generate_documentation",
	"generate_index_md",
	"get_edit_url",
	"get_source_url",
	"get_sphinx_conf_content",
	"get_theme_options",
	"heading",
	"is_public",
	"package_page",
	"python_literal",
	"sphinx_docs",
	"titled",
	"write_custom_css",
	"write_module_pages",
	"write_sidebar_nav",
	"write_version_switcher",
]

