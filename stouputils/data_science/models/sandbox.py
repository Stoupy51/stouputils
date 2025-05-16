""" Sandbox model implementation. (Where I try strange things)

Tested:

- ConvNeXtBase with input_shape=(1024, 1024, 3)
- Custom CNN architecture for implant classification (fixed / not fixed)

"""

# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
from __future__ import annotations

from keras.layers import (
	BatchNormalization,
	Conv2D,
	Input,
	MaxPooling2D,
	SpatialDropout2D,
)
from keras.models import Model

from ...print import warning
from ...decorators import simple_cache
from .base_keras import BaseKeras
from .model_interface import CLASS_ROUTINE_DOCSTRING, MODEL_DOCSTRING


class Sandbox(BaseKeras):
	def _get_base_model(self) -> Model:
		return self.custom_architecture()

	def custom_architecture(self) -> Model:
		""" Create a custom architecture for implant classification.

        This model uses a series of convolutional blocks with increasing depth,
        batch normalization, spatial and regular dropout for regularization.
        It's designed to detect features relevant to implant fixation status.

        Note: This is a custom architecture that does not use transfer learning.
        The transfer_learning attribute is ignored.

        Returns:
            Model: A Keras model without top layers for implant classification
        """
		if self.transfer_learning != "":
			warning(
				f"Transfer learning '{self.transfer_learning}' specified but not supported for custom architecture. "
				f"Using a model trained from scratch instead."
			)

		# Default input shape based on dataset loading defaults (224x224x3)
		input_shape: tuple[int, int, int] = (224, 224, 3)

		# Input layer
		inputs = Input(shape=input_shape)

		# Block 1: Initial feature extraction
		x = Conv2D(64, (3, 3), activation="relu", padding="same", name="block1_conv1")(inputs)
		x = BatchNormalization()(x)
		x = Conv2D(64, (3, 3), activation="relu", padding="same", name="block1_conv2")(x)
		x = BatchNormalization()(x)
		x = MaxPooling2D((2, 2), strides=(2, 2), name="block1_pool")(x)
		x = SpatialDropout2D(0.1)(x)

		# Block 2: Intermediate features
		x = Conv2D(128, (3, 3), activation="relu", padding="same", name="block2_conv1")(x)
		x = BatchNormalization()(x)
		x = Conv2D(128, (3, 3), activation="relu", padding="same", name="block2_conv2")(x)
		x = BatchNormalization()(x)
		x = MaxPooling2D((2, 2), strides=(2, 2), name="block2_pool")(x)
		x = SpatialDropout2D(0.1)(x)

		# Block 3: More complex features
		x = Conv2D(256, (3, 3), activation="relu", padding="same", name="block3_conv1")(x)
		x = BatchNormalization()(x)
		x = Conv2D(256, (3, 3), activation="relu", padding="same", name="block3_conv2")(x)
		x = BatchNormalization()(x)
		x = Conv2D(256, (3, 3), activation="relu", padding="same", name="block3_conv3")(x)
		x = BatchNormalization()(x)
		x = MaxPooling2D((2, 2), strides=(2, 2), name="block3_pool")(x)
		x = SpatialDropout2D(0.1)(x)

		# Block 4: Deep features
		x = Conv2D(512, (3, 3), activation="relu", padding="same", name="block4_conv1")(x)
		x = BatchNormalization()(x)
		x = Conv2D(512, (3, 3), activation="relu", padding="same", name="block4_conv2")(x)
		x = BatchNormalization()(x)
		x = Conv2D(512, (3, 3), activation="relu", padding="same", name="block4_conv3")(x)
		x = BatchNormalization()(x)
		x = MaxPooling2D((2, 2), strides=(2, 2), name="block4_pool")(x)
		x = SpatialDropout2D(0.1)(x)

		# Block 5: High-level abstract features
		x = Conv2D(512, (3, 3), activation="relu", padding="same", name="block5_conv1")(x)
		x = BatchNormalization()(x)
		x = Conv2D(512, (3, 3), activation="relu", padding="same", name="block5_conv2")(x)
		x = BatchNormalization()(x)
		x = Conv2D(512, (3, 3), activation="relu", padding="same", name="block5_conv3")(x)
		x = BatchNormalization()(x)

		# Create the model
		model = Model(inputs, x, name="implant_classifier")

		return model


# Docstrings
for model in [Sandbox]:
	model.__doc__ = MODEL_DOCSTRING.format(model=model.__name__)
	model.class_routine = simple_cache(model.class_routine)
	model.class_routine.__doc__ = CLASS_ROUTINE_DOCSTRING.format(model=model.__name__)

