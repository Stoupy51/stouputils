
# Imports
from src.stouputils.continuous_delivery import load_credentials, upload_to_github

# Get credentials
credentials: dict = load_credentials("~/stouputils/credentials.yml")

# Upload to GitHub
from upgrade import current_version
github_config: dict = {
	"project_name": "stouputils",
	"version": current_version,
	"build_folder": "",
}
changelog: str = upload_to_github(credentials, github_config)

