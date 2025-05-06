""" Configuration file for the project. """

# Imports
from ...decorators import LogLevels

# Configuration class
class DataScienceConfig:
	""" Configuration class for the project. """
	SEED: int = 42
	""" Seed for the random number generator. """

	ERROR_LOG: LogLevels = LogLevels.WARNING_TRACEBACK
	""" Log level for errors. """

	AUGMENTED_FILE_SUFFIX: str = "_aug_"
	""" Suffix for augmented files, ex: 'image_008_aug_1.png'. """

