
# Imports
import os
import stouputils as stp

# Constants
ROOT: str = os.path.dirname(os.path.abspath(__file__))
FOLDER_TO_TEST: str = f"{ROOT}/../src"

# Main
@stp.measure_time(stp.info, message="All doctests finished")
def main() -> None:
	stp.launch_tests(FOLDER_TO_TEST)

if __name__ == "__main__":
	main()

