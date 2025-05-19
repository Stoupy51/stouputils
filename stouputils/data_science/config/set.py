""" Configuration file for the project. """

# Imports
import os
from typing import Literal

from stouputils.decorators import LogLevels
from stouputils.io import get_root_path

# Environment variables
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "9"         # Suppress TensorFlow logging
os.environ["GRPC_VERBOSITY"] = "ERROR"           # Suppress gRPC logging


# Configuration class
class DataScienceConfig:
	""" Configuration class for the project. """

	# Common
	SEED: int = 42
	""" Seed for the random number generator. """

	ERROR_LOG: LogLevels = LogLevels.WARNING_TRACEBACK
	""" Log level for errors for all functions. """

	AUGMENTED_FILE_SUFFIX: str = "_aug_"
	""" Suffix for augmented files, e.g. 'image_008_aug_1.png'. """

	AUGMENTED_DIRECTORY_PREFIX: str = "aug_"
	""" Prefix for augmented directories, e.g. 'data/hip_implant' -> 'data/aug_hip_implant'. """

	PREPROCESSED_DIRECTORY_SUFFIX: str = "_preprocessed"
	""" Suffix for preprocessed directories, e.g. 'data/hip_implant' -> 'data/hip_implant_preprocessed'. """


	# Directories
	ROOT: str = get_root_path(__file__, go_up=3)
	""" Root directory of the project. """

	MLFLOW_FOLDER: str = f"{ROOT}/mlruns"
	""" Folder containing the mlflow data. """
	MLFLOW_URI: str = f"file://{MLFLOW_FOLDER}"
	""" URI to the mlflow data. """

	DATA_FOLDER: str = f"{ROOT}/data"
	""" Folder containing all the data (e.g. subfolders containing images). """

	TEMP_FOLDER: str = f"{ROOT}/temp"
	""" Folder containing temporary files (e.g. models checkpoints, plots, etc.). """

	LOGS_FOLDER: str = f"{ROOT}/logs"
	""" Folder containing the logs. """

	TENSORBOARD_FOLDER: str = f"{ROOT}/tensorboard"
	""" Folder containing the tensorboard logs. """


	# Behaviours
	TEST_SIZE: float = 0.2
	""" Size of the test set by default (0.2 means 80% training, 20% test). """

	VALIDATION_SIZE: float = 0.2
	""" Size of the validation set by default (0.2 means 80% training, 20% validation). """

	# Machine learning
	SAVE_MODEL: bool = False
	""" If the model should be saved in the mlflow folder using mlflow.*.save_model. """

	DO_SALIENCY_AND_GRADCAM: bool = True
	""" If the saliency and gradcam should be done during the run. """

	DO_LEARNING_RATE_FINDER: Literal[0, 1, 2] = 1
	""" If the learning rate finder should be done during the run.
	0: no, 1: only plot, 2: plot and use value for the remaining run
	"""

	DO_UNFREEZE_FINDER: Literal[0, 1, 2] = 0
	""" If the unfreeze finder should be done during the run.
	0: no, 1: only plot, 2: plot and use value for the remaining run
	"""

	DO_FIT_IN_SUBPROCESS: bool = True
	""" If the model should be fitted in a subprocess.
	Is memory efficient, and more stable. Turn it off only if you are having issues.

	Note: This allow a program to make lots of runs without getting killed by the OS for using too much resources.
	(e.g. LeaveOneOut Cross Validation, Grid Search, etc.)
	"""

	MIXED_PRECISION_POLICY: Literal["mixed_float16", "mixed_bfloat16", "float32"] = "mixed_float16"
	""" Mixed precision policy to use. Turn back to "float32" if you are having issues with a specific model or metrics.
	See: https://www.tensorflow.org/guide/mixed_precision
	"""

	TENSORFLOW_DEVICE: str = "/gpu:1"
	""" TensorFlow device to use. """



# Fix MLFLOW_URI for Windows by adding a missing slash
if os.name == "nt":
	DataScienceConfig.MLFLOW_URI = DataScienceConfig.MLFLOW_URI.replace("file:", "file:/")

