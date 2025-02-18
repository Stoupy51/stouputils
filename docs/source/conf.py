
# Imports
import os
import sys
from typing import Any
sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../../src'))
from upgrade import current_version		# Get version from pyproject.toml

# Project information
project: str = 'stouputils'
copyright: str = '2024, Stoupy'
author: str = 'Stoupy'
release: str = current_version

# General configuration
extensions: list[str] = [
	'sphinx.ext.autodoc',
	'sphinx.ext.napoleon',
	'sphinx.ext.viewcode',
	'sphinx.ext.githubpages',
	'sphinx.ext.intersphinx',
]

templates_path: list[str] = ['_templates']
exclude_patterns: list[str] = []

# HTML output options
html_theme: str = 'sphinx_rtd_theme'
html_static_path: list[str] = ['_static']

# Theme options
html_theme_options: dict[str, Any] = {
	'style_external_links': True,
}

# Add any paths that contain custom static files
html_static_path: list[str] = ['_static']

# Autodoc settings
autodoc_default_options: dict[str, bool | str] = {
	'members': True,
	'member-order': 'bysource',
	'special-members': False,
	'undoc-members': False,
	'private-members': False,
	'show-inheritance': True,
	'ignore-module-all': True,
	'exclude-members': '__weakref__'
}

# Tell autodoc to prefer source code over installed package
autodoc_mock_imports = []
always_document_param_types = True
add_module_names = False

# Tell Sphinx to look for source code in src directory
html_context = {
	'display_github': True,
	'github_user': 'Stoupy51',
	'github_repo': 'stouputils',
	'github_version': 'main',
	'conf_py_path': '/docs/source/',
	'source_suffix': '.rst',
}

# Only document items with docstrings
def skip_undocumented(app: Any, what: str, name: str, obj: Any, skip: bool, *args: Any, **kwargs: Any) -> bool:
	""" Skip members without docstrings.
	
	Args:
		app: Sphinx application
		what: Type of object
		name: Name of object
		obj: Object itself
		skip: Whether Sphinx would skip this
		options: Options given to autodoc directive
		
	Returns:
		bool: True if the member should be skipped
	"""
	if not obj.__doc__:
		return True
	return skip

def setup(app: Any) -> None:
	""" Set up the Sphinx application.
	
	Args:
		app: Sphinx application
	"""
	app.connect('autodoc-skip-member', skip_undocumented)

