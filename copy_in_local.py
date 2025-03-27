
# Imports
import stouputils as stp
import shutil

# Constants
ROOT: str = stp.get_root_path(__file__)
SOURCE: str = f"{ROOT}/stouputils"
DESTINATIONS: list[str] = [
    "C:/Users/Alexandre-PC/AppData/Local/Programs/Python/Python312/Lib/site-packages/stouputils",
    "C:/Users/1053914/AppData/Local/Programs/Python/Python312/Lib/site-packages/stouputils"
]

# Main
if __name__ == "__main__":
	for destination in DESTINATIONS:
		try:
			# Remove destination
			shutil.rmtree(destination, ignore_errors=True)

			# Copy source
			shutil.copytree(SOURCE, destination)
		except Exception as e:
			pass

	# Info
	stp.info("Copied stouputils to local Python's site-packages")

