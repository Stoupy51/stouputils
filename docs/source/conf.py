
# Imports
import os
import sys
from typing import Any
sys.path.insert(0, os.path.abspath('../..'))
from upgrade import current_version		# Get version from pyproject.toml

# Project information
project: str = 'Stouputils'
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

