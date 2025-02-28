
# Imports
import stouputils as stp
import time

# Functions
def is_even(n: int) -> bool:
	return n % 2 == 0

def multiple_args(a: int, b: int) -> int:
	return a * b

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
		multiple_args, args_2, use_starmap=True, desc="Multiple args", max_workers=2, verbose=1
	)
	stp.info(f"Results: {results_2}")

