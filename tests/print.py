
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

	# Test the new colored function with comprehensive text
	stp.infoc("""
══════════════════════════════════════════════════════════════════════════════════════
Testing the colored() function with Python 3.14 style formatting:

File Processing Example:
Failed to load /home/user/data.csv at line 42 in load_data() function. Got ValueError
when calling parse() with 100 items. Check file ./config.json or use open() to inspect.

Error Handling:
Caught KeyboardInterrupt in process_data() at line 256 in utils.py. The RuntimeError
was triggered when sum() tried to process 3.14 items. Use len() and map() to debug.

Complex Scenario:
Execute init() and setup() functions, then read C:\\Users\\data\\backup.zip with 512
bytes. If you get IndexError or FileNotFoundError, call close() to cleanup. Reference
line 128 in script.py. Also use type() and str() to verify. Found 1000 records with
average 45.67 value. Call filter() or max() for analysis.

Exception List:
Possible exceptions: ValueError, TypeError, AttributeError, RuntimeError, and
KeyboardInterrupt. Handle with try/except and inspect using vars() or getattr().

Final Summary:
Tests completed with 99 successes and 1 failure at ./logs/report.txt line 7 in
validate(). Use format() to display results or print() for debugging.
══════════════════════════════════════════════════════════════════════════════════════
""")

