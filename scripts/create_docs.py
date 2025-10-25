
# Imports
import sys

import stouputils.applications.automatic_docs as app
from stouputils.io import get_root_path

# Update documentation
if __name__ == "__main__":

	version: str | None = None
	if len(sys.argv) == 2:
		version = sys.argv[1]
	elif len(sys.argv) == 1:
		pass
	else:
		raise ValueError("Usage: python create_docs.py [version]")

	# Update documentation
	app.update_documentation(
		root_path=get_root_path(__file__, go_up=1),
		project="stouputils",
		author="Stoupy",
		copyright="2025, Stoupy",
		html_logo="https://avatars.githubusercontent.com/u/35665974",
		html_favicon="https://avatars.githubusercontent.com/u/35665974",
		github_user="Stoupy51",
		github_repo="stouputils",
		html_theme="sphinx_breeze_theme",
		version=version,
		skip_undocumented=True,
	)

