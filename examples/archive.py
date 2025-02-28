
# Imports
import stouputils as stp
from zipfile import ZipFile, BadZipFile

# Main
if __name__ == "__main__":
	PREFIX: str = "examples/archive"

	## Repair a corrupted zip file
	# Try to read the first file
	@stp.handle_error(BadZipFile)
	def read_file() -> None:
		with ZipFile(f"{PREFIX}/corrupted.zip", "r") as zip_file:
			stp.info(zip_file.read("pack.mcmeta"))
	read_file()

	# Repair it
	stp.repair_zip_file(f"{PREFIX}/corrupted.zip", f"{PREFIX}/repaired.zip")

	# Read the first file
	with ZipFile(f"{PREFIX}/repaired.zip", "r") as zip_file:
		stp.info(zip_file.read("pack.mcmeta"))

