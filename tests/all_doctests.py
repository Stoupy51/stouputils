
# Imports
import os
import sys

# Ensure the local stouputils package is used instead of any installed version in site-packages
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import stouputils
from stouputils import get_root_path, info, launch_tests, measure_time


# Main
@measure_time(printer=info, message="All doctests finished")
def main() -> None:
	FOLDER_TO_TEST: str = get_root_path(__file__, 1)
	if launch_tests(f"{FOLDER_TO_TEST}/stouputils") > 0:
		sys.exit(1)

if __name__ == "__main__":
	main()

