
# Imports
import stouputils as stp
from typing import Any

# Constants
ROOT: str = stp.get_root_path(__file__, go_up=1)
CURRENT_VERSION: str = stp.get_version_from_pyproject(f"{ROOT}/pyproject.toml")
CREDENTIALS_PATH: str = "~/stouputils/credentials.yml"
GITHUB_CONFIG: dict[str, Any] = {
	"project_name": "stouputils",
	"version": CURRENT_VERSION,
	"build_folder": f"{ROOT}/dist",
	"endswith": [
		f"{CURRENT_VERSION}.tar.gz",
		f"{CURRENT_VERSION}-py3-none-any.whl",
	],
}

# Main
if __name__ == "__main__":

	# Get credentials
	credentials: dict[str, Any] = stp.load_credentials(CREDENTIALS_PATH)

	# Upload to GitHub
	changelog: str = stp.upload_to_github(credentials, GITHUB_CONFIG)

