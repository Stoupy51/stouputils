""" Generation of the documentation landing page.

The default page is the README with a version selector and a module toctree appended.
Projects wanting something else pass their own callable as ``generate_index_function``.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ....lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from collections.abc import Callable

from ..common import generate_version_selector, get_versions_from_github


# Functions
def generate_index_md(
	readme_path: str,
	index_path: str,
	project: str,
	github_user: str,
	github_repo: str,
	get_versions_function: Callable[[str, str, int], list[str]] = get_versions_from_github,
	recent_minor_versions: int = 2,
) -> None:
	""" Generate `index.md` (MyST) from README.md content.

	This keeps the README content as Markdown (no conversion) and uses the MyST
	`toctree` directive to include module docs.

	Args:
		readme_path:           Path to the README.md file
		index_path:            Path where index.md should be created
		project:               Name of the project
		github_user:           GitHub username
		github_repo:           GitHub repository name
		get_versions_function: Function to get versions from GitHub
		recent_minor_versions: Number of recent minor versions to show all patches for. Defaults to 2
	"""
	# Read README content
	with open(readme_path, encoding="utf-8") as f:
		readme_content: str = f.read()

	# Generate version selector (markdown links)
	version_selector: str = generate_version_selector(
		github_user=github_user,
		github_repo=github_repo,
		get_versions_function=get_versions_function,
		recent_minor_versions=recent_minor_versions,
	)

	# Module documentation toctree (MyST)
	project_module: str = project.lower()
	module_docs: str = f"""
```{{toctree}}
:maxdepth: 10

modules/{project_module}
```
"""

	# Build final markdown content
	md_content: str = f"""
# ✨ Welcome to {project.capitalize()} Documentation ✨

{version_selector}

{readme_content}

---

## Module Documentation

{module_docs}
"""

	# Write the Markdown file
	with open(index_path, "w", encoding="utf-8") as f:
		f.write(md_content)

