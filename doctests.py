
# Imports
import os
from src.stouputils import launch_tests, measure_time, info

# Constants
ROOT: str = os.path.dirname(os.path.abspath(__file__))
FOLDER_TO_TEST: str = f"{ROOT}/src"

# Main
@measure_time(info, message="All doctests finished")
def main() -> None:
	launch_tests(FOLDER_TO_TEST)

if __name__ == "__main__":
	main()

