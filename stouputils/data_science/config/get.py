""" Load configuration from the set.py file and handle some special cases.

Proper way to get the configuration is by importing this module, not the set.py file directly.
"""

# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
import os
from typing import Any

from .set import DataScienceConfig

# Special cases
# Hide GPU when using CPU
if DataScienceConfig.TENSORFLOW_DEVICE.lower().startswith("/cpu"):
	os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Precise which GPU we use
elif DataScienceConfig.TENSORFLOW_DEVICE.lower().startswith("/gpu"):
	os.environ["CUDA_VISIBLE_DEVICES"] = DataScienceConfig.TENSORFLOW_DEVICE.split(":")[-1]

	# Configure TensorFlow (if available)
	try:
		from tensorflow import config as tf_config

		# Get the physical devices
		physical_devices: list[Any] = tf_config.list_physical_devices("GPU")

		# Configure TensorFlow GPU memory management to allocate memory dynamically
		# This prevents TensorFlow from allocating all GPU memory upfront
		# Instead, memory will grow as needed, allowing better resource sharing
		for device in physical_devices:
			tf_config.experimental.set_memory_growth(device, True)

		# Disable eager execution mode in TensorFlow
		# This improves performance by allowing TensorFlow to create an optimized graph
		# of operations instead of executing operations one by one (at the cost of debugging difficulty)
		tf_config.run_functions_eagerly(False)
	except ImportError:
		pass

	# Enable mixed precision training (if available)
	try:
		from keras import mixed_precision
		mixed_precision.set_global_policy(DataScienceConfig.MIXED_PRECISION_POLICY)
	except ImportError:
		pass

