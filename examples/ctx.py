
# Imports
import stouputils as stp
import sys
import os

# Main
if __name__ == "__main__":

	# Test Muffle
	with stp.Muffle(mute_stderr=True):
		print("Nothing")
		print("here", file=sys.stderr)
		stp.info("will be")
		stp.info("printed", file=sys.stderr)

	# Test TeeMultiOutput
	f = open("logfile.txt", "w")
	original_stderr = sys.stderr
	stp.multithreading(abs, range(10000), desc="Calculating absolute values", verbose=True)
	sys.stderr = stp.TeeMultiOutput(sys.stderr, f)
	stp.multithreading(abs, range(10000), desc="Calculating absolute values", verbose=True)
	sys.stderr = original_stderr
	f.close()

	# Test LogToFile
	OUTPUT_PATH: str = "_super_idol_de_xiao_rong.log"
	with stp.LogToFile(OUTPUT_PATH):
		stp.info("""
Why did the programmer always bring a ladder to work?
Because they spent so much time debugging and climbing through their log files!
""")

	stp.breakpoint("Press Enter to continue...")
	os.remove(OUTPUT_PATH)

