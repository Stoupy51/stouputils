""" Configuration file for the project. """

# Imports
from ...decorators import LogLevels

# Configuration class
class DataScienceConfig:
	""" Configuration class for the project. """
	NONE: None = None
	ERROR_LOG: LogLevels = LogLevels.WARNING_TRACEBACK
	pass

