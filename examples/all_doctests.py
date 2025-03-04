
# Imports
import stouputils as stp

# Main
@stp.measure_time(stp.info, message="All doctests finished")
def main() -> None:
	FOLDER_TO_TEST: str = stp.get_root_path(__file__, 1) + "/src"
	stp.launch_tests(FOLDER_TO_TEST)

if __name__ == "__main__":
	main()

