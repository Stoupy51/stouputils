
# Imports
import stouputils as stp

# Main
if __name__ == "__main__":

	# Handle exceptions
	@stp.handle_error(
		exceptions=ZeroDivisionError,
		message="Debugging: The process of removing software bugs, and putting in new ones",
		error_log=stp.LogLevels.WARNING_TRACEBACK
	)
	def raise_value_error():
		return 1 / 0

	@stp.handle_error()
	def raise_value_error_2():
		return 1 / 0

	raise_value_error()			# This will show the error using stp.warning
	raise_value_error_2()		# This will show the error using stp.error
