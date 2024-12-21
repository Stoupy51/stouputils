
# Imports
from stouputils import load_credentials, upload_to_github, clean_path, super_copy
from typing import Any
from upgrade import current_version
import shutil
import os

# Constants
ROOT: str = clean_path(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH: str = "~/stouputils/credentials.yml"
TEMPORARY_FOLDER: str = f"{ROOT}/__temporary__"
GITHUB_CONFIG: dict[str, Any] = {
	"project_name": "stouputils",
	"version": current_version,
	"build_folder": TEMPORARY_FOLDER,
}

# Get credentials
credentials: dict[str, Any] = load_credentials(CREDENTIALS_PATH)

# Get the latest build in a temporary folder
try:
	os.makedirs(TEMPORARY_FOLDER, exist_ok=True)
	super_copy(f"{ROOT}/dist/stouputils-{current_version}.tar.gz", TEMPORARY_FOLDER)
	super_copy(f"{ROOT}/dist/stouputils-{current_version}-py3-none-any.whl", TEMPORARY_FOLDER)

	# Upload to GitHub
	changelog: str = upload_to_github(credentials, GITHUB_CONFIG)

finally:
	# Delete the temporary folder
	shutil.rmtree(TEMPORARY_FOLDER)

