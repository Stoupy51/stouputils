
# Imports
import stouputils as stp
import sys
import os

# Main
if __name__ == "__main__":
	
	with stp.Muffle(mute_stderr=True):
		print("Nothing")
		print("here", file=sys.stderr)
		stp.info("will be")
		stp.info("printed", file=sys.stderr)

	OUTPUT_PATH: str = "_super_idol_de_xiao_rong.log"
	with stp.LogToFile(OUTPUT_PATH):
		stp.info("""
Why did the programmer always bring a ladder to work?
Because they spent so much time debugging and climbing through their log files!
""")
		
	stp.breakpoint("Press Enter to continue...")
	os.remove(OUTPUT_PATH)

