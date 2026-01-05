
# Imports
import time

import stouputils as stp

# Main
if __name__ == "__main__":
	stp.info("Hello", "World")
	time.sleep(0.5)
	stp.info("Hello", "World")
	time.sleep(0.5)
	stp.info("Hello", "World")
	time.sleep(0.5)
	stp.info("Not Hello World !")
	time.sleep(0.5)
	stp.info("Hello", "World")
	time.sleep(0.5)
	stp.info("Hello", "World")

	# All remaining print functions
	stp.debug("Hello", "World")
	stp.suggestion("Hello", "World")
	stp.progress("Hello", "World")
	stp.warning("Hello", "World")
	stp.error("Hello", "World", exit=False)
	stp.whatisit("Hello", "World")

