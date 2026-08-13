""" Code forge URL conventions, used to link a documented object back to its source.

Every forge agrees that a URL needs a repository, a branch and a path, and no two of them agree on the order.
This module holds that knowledge in one table so the rest of the generator never has to care.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ....lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from dataclasses import dataclass


# Classes
@dataclass(frozen=True)
class ForgeUrls:
	""" URL patterns of a code forge, built from a repository URL. """

	edit: str
	""" Pattern for editing a file, with ``{repo}``, ``{branch}`` and ``{path}`` placeholders. """

	blob: str
	""" Pattern for viewing a file, with the same placeholders. """


# Constants
FORGES: dict[str, ForgeUrls] = {
	"github":    ForgeUrls(edit="{repo}/edit/{branch}/{path}",          blob="{repo}/blob/{branch}/{path}"),
	"gitlab":    ForgeUrls(edit="{repo}/-/edit/{branch}/{path}",        blob="{repo}/-/blob/{branch}/{path}"),
	"bitbucket": ForgeUrls(edit="{repo}/src/{branch}/{path}?mode=edit", blob="{repo}/src/{branch}/{path}"),
	"codeberg":  ForgeUrls(edit="{repo}/_edit/{branch}/{path}",         blob="{repo}/src/branch/{branch}/{path}"),
}
""" Path conventions of each supported forge, since no two of them agree on where to put the branch. """


# Functions
def get_source_url(repo_url: str, repo_provider: str, repo_branch: str) -> str:
	""" Build the ``linkcode`` template pointing at a module's source file.

	Args:
		repo_url      (str): Repository URL, ex: "https://github.com/Stoupy51/stouputils"
		repo_provider (str): Which key of :data:`FORGES` describes the repository URL
		repo_branch   (str): Branch the source links point at
	Returns:
		str: URL with a remaining ``{filename}`` placeholder, empty when no repository is known

	Examples:
		>>> get_source_url("https://github.com/Stoupy51/stouputils", "github", "main")
		'https://github.com/Stoupy51/stouputils/blob/main/{filename}.py'
		>>> get_source_url("", "github", "main")
		''
	"""
	if not repo_url:
		return ""
	return FORGES[repo_provider].blob.format(repo=repo_url.rstrip("/"), branch=repo_branch, path="{filename}.py")


def get_edit_url(repo_url: str, repo_provider: str, repo_branch: str, edit_link_path: str) -> str:
	""" Build the "edit this page" template the theme fills with the page path.

	Args:
		repo_url       (str): Repository URL, ex: "https://github.com/Stoupy51/stouputils"
		repo_provider  (str): Which key of :data:`FORGES` describes the repository URL
		repo_branch    (str): Branch the edit links point at
		edit_link_path (str): Where the Sphinx sources are tracked, ex: "docs/source"
	Returns:
		str: URL ending in the theme's ``%s`` placeholder, empty when either argument is missing

	Examples:
		>>> get_edit_url("https://gitlab.com/g/p", "gitlab", "main", "docs/source")
		'https://gitlab.com/g/p/-/edit/main/docs/source/%s'
		>>> get_edit_url("https://gitlab.com/g/p", "gitlab", "main", "")
		''
	"""
	if not (repo_url and edit_link_path):
		return ""
	edit_path: str = f"{edit_link_path.strip('/')}/%s"
	return FORGES[repo_provider].edit.format(repo=repo_url.rstrip("/"), branch=repo_branch, path=edit_path)

