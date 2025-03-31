
# Imports
import stouputils as stp
from typing import Any

# Main
if __name__ == "__main__":

	path: str = "C:\\\\Users\\\\Stoupy\\\\Documents\\\\test.txt"
	path = stp.clean_path(path)
	stp.info(path)

	tilde_path: str = "~/Desktop/OnlyFansIncome.txt"
	tilde_path = stp.replace_tilde(tilde_path)
	stp.info(tilde_path)

	this_folder_dont_exist: str = "./this_folder_dont_exist/a/c/feff/efefe/a"
	with stp.super_open(this_folder_dont_exist, "w") as file:	# Automatically create the folder
		file.write("Hello, world!")

	# Copy a file to a folder, or rename the copied file
	stp.super_copy("LICENSE", "this_folder_dont_exist/a/")           # .../a/LICENSE
	stp.super_copy("LICENSE", "this_folder_dont_exist/a/LICENSE_2")  # .../a/LICENSE_2
	stp.breakpoint("Waiting for input to continue code execution...")

	# Dump a JSON file with a specified indentation depth
	data: dict[str, Any] = {"name": "John", "array": [[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]]}
	stp.info("\n", stp.super_json_dump(data, max_level=2))

	# Remove the folder
	import shutil
	shutil.rmtree("this_folder_dont_exist")

