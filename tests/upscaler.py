
# Imports
import stouputils.applications.upscaler as app
from stouputils.io.path import get_root_path

# Constants
ROOT: str = get_root_path(__file__) + "/upscaler"
INPUT_FOLDER: str = f"{ROOT}/input"
PROGRESS_FOLDER: str = f"{ROOT}/progress"
OUTPUT_FOLDER: str = f"{ROOT}/output"

# Main
if __name__ == "__main__":
	app.video_upscaler_cli(INPUT_FOLDER, PROGRESS_FOLDER, OUTPUT_FOLDER)

