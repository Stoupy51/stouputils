
# Imports
import stouputils as stp

# Constants
ROOT: str = stp.get_root_path(__file__, go_up=1)
REPOSITORY: str = "stouputils"
DIST_DIRECTORY: str = f"{ROOT}/dist"
LAST_FILES: int = 1
ENDWITH: str = ".tar.gz"

if __name__ == "__main__":

	stp.pypi_full_routine(
		repository=REPOSITORY,
		dist_directory=DIST_DIRECTORY,
		last_files=LAST_FILES,
		endswith=ENDWITH,
	)

