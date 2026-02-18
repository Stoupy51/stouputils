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
# Imports
from .common import *
from .sphinx import *
from .zensical import *

# Deprecated
from ...decorators.deprecated import deprecated
@deprecated(message="Use sphinx_docs or zensical_docs instead", version="1.23.0")
def update_documentation(*args: object, **kwargs: object) -> None:
    return sphinx_docs(*args, **kwargs)

