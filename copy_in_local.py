
# Imports
import stouputils as stp
import shutil

# Constants
ROOT: str = stp.get_root_path(__file__)
SOURCE: str = f"{ROOT}/src/stouputils"
DESTINATION: str = "C:/Users/Alexandre-PC/AppData/Local/Programs/Python/Python310/Lib/site-packages/stouputils"

# Main
if __name__ == "__main__":

	# Remove destination
	shutil.rmtree(DESTINATION, ignore_errors=True)

	# Copy source
	shutil.copytree(SOURCE, DESTINATION)

	# Info
	stp.info("Copied stouputils to local Python's site-packages")

