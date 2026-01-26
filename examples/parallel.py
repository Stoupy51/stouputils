
# Imports
import time

import stouputils as stp

# Constants
ROOT: str = stp.get_root_path(__file__)

# Functions
def is_even(n: int) -> bool:
	return n % 2 == 0

def multiple_args(a: int, b: int) -> int:
	return a * b


# Subprocess example function (must be top-level for pickling)
def child_messages() -> str:
	import sys
	print("Child stdout message")
	print("Child stderr message", file=sys.stderr)
	return "child_done"

# Main
if __name__ == "__main__":

	# Multi-threading (blazingly fast for IO-bound tasks)
	args_1: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
	results_1: list[bool] = stp.multithreading(is_even, args_1)
	stp.info(f"Results: {results_1}")

	# Multi-processing (better for CPU-bound tasks)
	time.sleep(1)
	args_2: list[tuple[int, int]] = [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10)]
	results_2: list[int] = stp.multiprocessing(
		multiple_args, args_2, use_starmap=True, desc="Multiple args", max_workers=2
	)
	stp.info(f"Results: {results_2}")

	# Run a function in a subprocess and capture both stdout and stderr
	with stp.LogToFile(f"{ROOT}/parallel_subprocess.log"):
		res = stp.run_in_subprocess(child_messages, capture_output=True)
		stp.info(f"Subprocess returned: {res}")

