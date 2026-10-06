""" Generation of the documentation landing page.

The default page is the README, with a hidden toctree making the API reference a tab of the header.
Projects wanting something else pass their own callable as ``generate_index_function``.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ....lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY


# Functions
def generate_index_md(readme_path: str, index_path: str, project: str) -> None:
	""" Generate `index.md` (MyST) from README.md content, kept as Markdown.

	Args:
		readme_path: Path to the README.md file
		index_path:  Path where index.md should be created
		project:     Name of the project, lowercased into the name of its root package
	"""
	with open(readme_path, encoding="utf-8") as f:
		readme_content: str = f.read()

	md_content: str = f"""
# ✨ Welcome to {project.capitalize()} Documentation ✨

{readme_content}

```{{toctree}}
:hidden:

modules/{project.lower()}
```
"""

	# Write the Markdown file
	with open(index_path, "w", encoding="utf-8") as f:
		f.write(md_content)

