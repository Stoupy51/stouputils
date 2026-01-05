
# Imports
import stouputils as stp

# Main
if __name__ == "__main__":

	# Example with numbers
	numbers: list[int] = [1, 2, 3, 2, 1, 4, 3]
	unique_numbers: list[int] = stp.unique_list(numbers)
	stp.info(f"Original numbers: {numbers}")
	stp.info(f"Unique numbers: {unique_numbers}")

	# Example with sets using different methods
	s1: set[int] = {1, 2, 3}
	s2: set[int] = {2, 3, 4}
	s3: set[int] = {1, 2, 3}
	sets: list[set[int]] = [s1, s2, s1, s1, s3, s2, s3]

	# Using id method (keeps s1 and s3 as separate objects)
	unique_sets_id: list[set[int]] = stp.unique_list(sets, method="id")
	stp.info(f"Unique sets (id method): {unique_sets_id}")

	# Using str method (combines s1 and s3 as they have same string representation)
	unique_sets_str: list[set[int]] = stp.unique_list(sets, method="str")
	stp.info(f"Unique sets (str method): {unique_sets_str}")


