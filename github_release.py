
# Imports
from stouputils import load_credentials, upload_to_github, clean_path
from typing import Any
from upgrade import current_version
import os

# Constants
ROOT: str = clean_path(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH: str = "~/stouputils/credentials.yml"
GITHUB_CONFIG: dict[str, Any] = {
	"project_name": "stouputils",
	"version": current_version,
	"build_folder": f"{ROOT}/dist",
	"endswith": [
		f"{current_version}.tar.gz",
		f"{current_version}-py3-none-any.whl",
	],
}

# Get credentials
credentials: dict[str, Any] = load_credentials(CREDENTIALS_PATH)

# Upload to GitHub
changelog: str = upload_to_github(credentials, GITHUB_CONFIG)

