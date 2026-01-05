""" Xception model implementation.

This module provides a wrapper class for the Xception model, a deep convolutional neural network
designed for efficient image classification. Xception uses depthwise separable convolutions,
which significantly reduce the number of parameters and computational complexity compared to
standard convolutional layers.

Available models:
- Xception: The standard Xception model

The model supports transfer learning from ImageNet pre-trained weights.
"""
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
from __future__ import annotations

from keras.models import Model
from keras.src.applications.xception import Xception as Xception_keras

from ....decorators import simple_cache
from ..base_keras import BaseKeras
from ..model_interface import CLASS_ROUTINE_DOCSTRING, MODEL_DOCSTRING


# Base class
class Xception(BaseKeras):
	def _get_base_model(self) -> Model:
		return Xception_keras(include_top=False, classes=self.num_classes)


# Docstrings
for model in [Xception]:
	model.__doc__ = MODEL_DOCSTRING.format(model=model.__name__)
	model.class_routine = simple_cache(model.class_routine)
	model.class_routine.__doc__ = CLASS_ROUTINE_DOCSTRING.format(model=model.__name__)

