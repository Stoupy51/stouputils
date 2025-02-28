
# Imports
import os
import shutil
import subprocess
import sys
from stouputils import clean_path, handle_error, warning, simple_cache
from stouputils.continuous_delivery.github import version_to_float
clean_exec: str = clean_path(sys.executable)

conf_content: str = """
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
	'furo.sphinxext',
]

templates_path: list[str] = ['_templates']
exclude_patterns: list[str] = []

# HTML output options
html_theme: str = 'furo'
html_static_path: list[str] = ['_static']
html_logo: str = 'https://avatars.githubusercontent.com/u/35665974'
html_title: str = 'stouputils'
html_favicon: str = 'https://avatars.githubusercontent.com/u/35665974'

# Theme options
html_theme_options: dict[str, Any] = {
	'light_css_variables': {
		'color-brand-primary': '#2980B9',
		'color-brand-content': '#2980B9',
		'color-admonition-background': '#E8F0F8',
	},
	'dark_css_variables': {
		'color-brand-primary': '#56B4E9',
		'color-brand-content': '#56B4E9',
		'color-admonition-background': '#1F262B',
	},
	'sidebar_hide_name': False,
	'navigation_with_keys': True,
	'announcement': 'This is the latest documentation of stouputils',
	'footer_icons': [
		{
			'name': 'GitHub',
			'url': 'https://github.com/Stoupy51/stouputils',
			'html': '<i class="fab fa-github-square"></i>',
			'class': '',
		},
	],
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
	'default_mode': 'dark',
}

# Only document items with docstrings
def skip_undocumented(app: Any, what: str, name: str, obj: Any, skip: bool, *args: Any, **kwargs: Any) -> bool:
	if not obj.__doc__:
		return True
	return skip

def setup(app: Any) -> None:
	app.connect('autodoc-skip-member', skip_undocumented)
"""

@simple_cache()
def get_versions_from_github() -> list[str]:
	""" Get list of versions from GitHub gh-pages branch.

	Returns:
		list[str]: List of versions, with 'latest' as first element
	"""
	import requests
	version_list: list[str] = []
	try:
		response = requests.get("https://api.github.com/repos/Stoupy51/stouputils/contents?ref=gh-pages")
		if response.status_code == 200:
			contents = response.json()
			version_list = ["latest"] + sorted(
				[d["name"].replace("v", "") for d in contents 
				if d["type"] == "dir" and d["name"].startswith("v")],
				key=version_to_float,
				reverse=True
			)
	except Exception as e:
		warning(f"Failed to get versions from GitHub: {e}")
		version_list = ["latest"]
	return version_list

def generate_index_rst(readme_path: str, index_path: str) -> None:
	""" Generate index.rst from README.md content.
	
	Args:
		readme_path (str): Path to the README.md file
		index_path (str): Path where index.rst should be created
	"""
	with open(readme_path, 'r', encoding="utf-8") as f:
		readme_content: str = f.read()
	
	# Convert markdown badges to RST format
	badges_rst: str = """
.. image:: https://img.shields.io/github/v/release/Stoupy51/stouputils?logo=github&label=GitHub
  :target: https://github.com/Stoupy51/stouputils/releases/latest

.. image:: https://img.shields.io/pypi/dm/stouputils?logo=python&label=PyPI%20downloads
  :target: https://pypi.org/project/stouputils/
"""
	
	# Generate version selector
	version_selector: str = """

**Versions**: """
	
	# Get versions from GitHub
	version_list: list[str] = get_versions_from_github()
	
	# Create version links
	version_links: list[str] = []
	for version in version_list:
		if version == 'latest':
			version_links.append("`latest <../latest/index.html>`_")
		else:
			version_links.append(f"`v{version} <../v{version}/index.html>`_")
	
	version_selector += ", ".join(version_links)
	
	# Extract sections while preserving emojis
	overview_section: str = readme_content.split('# 📚 Project Overview')[1].split('\n#')[0].strip()
	file_tree_section: str = readme_content.split('# 🚀 Project File Tree')[1].split('\n#')[0].strip()
	file_tree_section = file_tree_section.replace('```bash', '').replace('```', '').strip()
	file_tree_section = "\n".join([f"   {line}" for line in file_tree_section.split('\n')])
	
	# Generate module documentation section
	module_docs: str = ".. toctree::\n   :maxdepth: 10\n   :caption: Contents:\n\n"
	
	# Add base module
	module_docs += "   modules/stouputils\n\n"
	
	# Generate the RST content with emojis and proper title underlines
	rst_content: str = f"""
🛠️ Welcome to Stouputils Documentation
=======================================

{badges_rst}

{version_selector}

📚 Overview
-----------
{overview_section.replace("<br>", " ")}

🚀 Project Structure
-------------------
.. code-block:: bash

{file_tree_section}

📖 Module Documentation
----------------------
{module_docs}

⚡ Indices and Tables
===================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
"""
	
	# Write the RST file
	with open(index_path, 'w', encoding="utf-8") as f:
		f.write(rst_content)

def generate_conf_py(conf_path: str) -> None:
	""" Generate conf.py file.
	
	Args:
		conf_path (str): Path where conf.py should be created
	"""
	with open(conf_path, 'w', encoding="utf-8") as f:
		f.write(conf_content)

@handle_error()
def update_documentation(version: str | None = None) -> None:
	""" Update the Sphinx documentation.
	This script will:
	1. Create necessary directories if they don't exist
	2. Generate module documentation using sphinx-apidoc
	3. Build HTML documentation for specific version if provided

	Args:
		version (str | None): Version to build documentation for. If None, builds for latest
	"""
	# Get the project root directory (parent of scripts folder)
	root_dir: str = clean_path(os.path.dirname(os.path.dirname(__file__)))
	docs_dir: str = clean_path(os.path.join(root_dir, "docs"))
	source_dir: str = clean_path(os.path.join(docs_dir, "source"))
	modules_dir: str = clean_path(os.path.join(source_dir, "modules"))

	# Modify build directory if version is specified
	build_dir: str = "html/latest" if not version else f"html/v{version}"
	
	# Create directories if they don't exist
	os.makedirs(modules_dir, exist_ok=True)
	os.makedirs(clean_path(os.path.join(source_dir, "_static")), exist_ok=True)
	os.makedirs(clean_path(os.path.join(source_dir, "_templates")), exist_ok=True)

	# Generate index.rst from README.md
	readme_path: str = clean_path(os.path.join(root_dir, "README.md"))
	index_path: str = clean_path(os.path.join(source_dir, "index.rst"))
	generate_index_rst(readme_path, index_path)

	# Clean up old module documentation
	if os.path.exists(modules_dir):
		shutil.rmtree(modules_dir)
		os.makedirs(modules_dir)

	# Update conf.py to include version selector
	version_list: list[str] = get_versions_from_github()
	
	# Update html_context in conf.py
	global conf_content
	conf_content = conf_content.replace(
		"html_context = {",
		f"""html_context = {{
	'versions': {version_list},
	'current_version': 'latest' if not {repr(version)} else {repr(version)},"""
	)

	# Generate docs/source/conf.py
	conf_path: str = clean_path(os.path.join(source_dir, "conf.py"))
	generate_conf_py(conf_path)

	# Generate module documentation using python -m
	subprocess.run([
		clean_exec,
		"-m", "sphinx.ext.apidoc",
		"-o", modules_dir,      # Output directory
		"-f",                   # Force overwrite
		"-e",                   # Put documentation for each module on its own page
		"-M",                   # Put module documentation before submodule documentation
		"--no-toc",             # Don't create a table of contents file
		"-P",                   # Include private modules
		"--implicit-namespaces",# Handle implicit namespaces
		"--module-first",       # Put module documentation before submodule documentation
		clean_path(os.path.join(root_dir, "src/stouputils")),  # Source code directory
	], check=True)

	# Build HTML documentation using python -m
	subprocess.run([
		clean_exec,
		"-m", "sphinx",
		"-b", "html",           # Build HTML
		"-a",                   # Write all files
		source_dir,             # Source directory
		clean_path(f"{docs_dir}/build/{build_dir}"),  # Output directory
	], check=True)

	print("Documentation updated successfully!")
	print(f"You can view the documentation by opening {docs_dir}/build/{build_dir}/index.html")

if __name__ == "__main__":
	if len(sys.argv) == 2:
		update_documentation(sys.argv[1].replace("v", ""))	# Remove "v" from version just in case
	elif len(sys.argv) == 1:
		update_documentation()
	else:
		raise ValueError("Usage: python create_docs.py [version]")

