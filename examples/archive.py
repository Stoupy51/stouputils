
# Imports
from zipfile import BadZipFile, ZipFile

import stouputils as stp

# Main
if __name__ == "__main__":
	PREFIX: str = "examples/archive"

	## Repair a corrupted zip file
	# Try to read the first file
	try:
		with ZipFile(f"{PREFIX}/corrupted_1.zip", "r") as zip_file:
			stp.info(zip_file.read("pack.mcmeta"))
	except BadZipFile as e:
		stp.warning(f"Failed to read corrupted zip file: {e}")
		stp.info("Attempting to repair the zip file...")

	# Repair it
	stp.repair_zip_file(f"{PREFIX}/corrupted_1.zip", f"{PREFIX}/repaired_1.zip")

	# Read the first file
	with ZipFile(f"{PREFIX}/repaired_1.zip", "r") as zip_file:
		stp.info(zip_file.read("pack.mcmeta"))

	## Repair a second corrupted zip file (more complex)
	stp.repair_zip_file(f"{PREFIX}/corrupted_2.zip", f"{PREFIX}/repaired_2.zip")

