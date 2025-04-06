
# Imports
import sys
import stouputils as stp
from stouputils.applications import automatic_docs

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
	automatic_docs.update_documentation(
		root_path=stp.get_root_path(__file__, go_up=1),
		project="stouputils",
		author="Stoupy",
		copyright="2025, Stoupy",
		html_logo="https://avatars.githubusercontent.com/u/35665974",
		html_favicon="https://avatars.githubusercontent.com/u/35665974",
		github_user="Stoupy51",
		github_repo="stouputils",
		html_theme="pydata_sphinx_theme",
		version=version,
		skip_undocumented=True,
	)

