
# Imports
import os
import shutil
import sys

import stouputils as stp

# Constants
ROOT: str = stp.get_root_path(__file__)

# Main
if __name__ == "__main__":

	# Generate stubs full routine
	os.system(f"{sys.executable} {ROOT}/scripts/generate_stubs.py")

	# Increment version in pyproject.toml
	minor_or_patch = "patch" if sys.argv[-1] != "minor" else "minor"
	os.system(f"uv version --bump {minor_or_patch}")

	# PyPI full routine (now using uv)
	shutil.rmtree(f"{ROOT}/dist")
	os.system("uv build")
	os.system("uv publish")

