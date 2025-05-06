""" Configuration file for the project. """

# Imports
import os
from .set import DataScienceConfig

# Environment variables
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "9"         # Suppress TensorFlow logging (because it's annoying as hell)
os.environ["GRPC_VERBOSITY"] = "ERROR"           # Suppress gRPC logging


DataScienceConfig.SEED = 42


### Strange things below, don't look at them

# ## Setup MLFLOW_TRACKING_URI
# # If we are on Windows, we need to have 3 slashes in the URI
# if os.name == "nt" and DataScienceConfig.MLFLOW_TRACKING_URI.startswith("file://"):
# 	is_3_slash: bool = DataScienceConfig.MLFLOW_TRACKING_URI.startswith("file:///")
# 	if not is_3_slash:
# 		DataScienceConfig.MLFLOW_TRACKING_URI = DataScienceConfig.MLFLOW_TRACKING_URI.replace("file:", "file://")

# # Memory profiler
# memory_profiler: IO[Any] | None = super_open(DataScienceConfig.MEMORY_PROFILER_FILE, "a") if DataScienceConfig.MEMORY_PROFILER_FILE else None

