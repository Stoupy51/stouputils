
# Imports
import time

import stouputils as stp

# Main
if __name__ == "__main__":

	# Cache the result of the function and measure the time it takes to execute
	@stp.measure_time(message="Time taken to execute long_function")
	@stp.simple_cache()
	def long_function() -> dict[str, int]:
		stp.info("Starting long function...")
		time.sleep(1)
		stp.info("Long function finished!")
		return {"a": 1, "b": 2}

	a = long_function()		# Takes 1 second
	b = long_function()		# Takes 0 second
	stp.info(f"a: {a}, b: {b}, a is b: {a is b}")
	b["c"] = 3
	stp.info(f"a has been modified because a is b: {a}")

	# Silent decorator
	@stp.silent
	def silent_function():
		print("ON THE CONSOLE")
	silent_function()

