""" Documentation generation utilities.

This subpackage provides a comprehensive set of utilities for automatically generating
and managing Sphinx or Zensical documentation for Python projects. It handles the creation
of configuration files, index pages, version management, and HTML generation.

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

# ruff: noqa: I001
# Lazy imports (PEP 810), ignored before Python 3.15
from ...lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .common import (
	check_base_dependencies as check_base_dependencies,
	download_asset as download_asset,
	generate_redirect_html as generate_redirect_html,
	generate_version_selector as generate_version_selector,
	get_versions_from_github as get_versions_from_github,
)
from .docstring import (
	DIRECTIVE_PATTERN as DIRECTIVE_PATTERN,
	VERBATIM_DIRECTIVES as VERBATIM_DIRECTIVES,
	connect_docstring_fixes as connect_docstring_fixes,
	fix_doctest_blocks as fix_doctest_blocks,
	process_docstring as process_docstring,
)
from .sphinx import (
	CUSTOM_CSS as CUSTOM_CSS,
	DEFAULT_DARK_STYLE as DEFAULT_DARK_STYLE,
	DEFAULT_LIGHT_STYLE as DEFAULT_LIGHT_STYLE,
	FORGES as FORGES,
	ForgeUrls as ForgeUrls,
	VSCodeDarkPlusStyle as VSCodeDarkPlusStyle,
	VSCodeLightPlusStyle as VSCodeLightPlusStyle,
	VSCodeSemanticFilter as VSCodeSemanticFilter,
	check_dependencies as check_dependencies,
	get_edit_url as get_edit_url,
	get_source_url as get_source_url,
	get_sphinx_conf_content as get_sphinx_conf_content,
	get_theme_options as get_theme_options,
	python_literal as python_literal,
	sphinx_docs as sphinx_docs,
	write_custom_css as write_custom_css,
)
from .zensical import (
	generate_api_pages as generate_api_pages,
	generate_documentation as generate_documentation,
	generate_index_md as generate_index_md,
	get_zensical_config_content as get_zensical_config_content,
	zensical_docs as zensical_docs,
)

# Deprecated
from ...decorators.deprecation import deprecated
from typing import Any
@deprecated(message="Use sphinx_docs or zensical_docs instead", version="1.23.0")
def update_documentation(*args: Any, **kwargs: Any) -> None:
    return sphinx_docs(*args, **kwargs)

