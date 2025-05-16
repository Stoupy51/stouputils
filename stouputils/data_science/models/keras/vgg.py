""" VGG models implementation.

This module provides wrapper classes for the VGG family of models from the Keras applications.
VGG models are characterized by their simplicity, using only 3x3 convolutional layers
stacked on top of each other with increasing depth.

Available models:
- VGG16: 16-layer model with 13 convolutional layers and 3 fully connected layers
- VGG19: 19-layer model with 16 convolutional layers and 3 fully connected layers

Both models support transfer learning from ImageNet pre-trained weights.
"""
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
from __future__ import annotations

from keras.models import Model
from keras.src.applications.vgg16 import VGG16 as VGG16_keras  # noqa: N811
from keras.src.applications.vgg19 import VGG19 as VGG19_keras  # noqa: N811

from ....decorators import simple_cache
from ..base_keras import BaseKeras
from ..model_interface import CLASS_ROUTINE_DOCSTRING, MODEL_DOCSTRING


# Base class
class VGG19(BaseKeras):
	def _get_base_model(self) -> Model:
		return VGG19_keras(include_top=False, classes=self.num_classes)
class VGG16(BaseKeras):
	def _get_base_model(self) -> Model:
		return VGG16_keras(include_top=False, classes=self.num_classes)


# Docstrings
for model in [VGG19, VGG16]:
	model.__doc__ = MODEL_DOCSTRING.format(model=model.__name__)
	model.class_routine = simple_cache(model.class_routine)
	model.class_routine.__doc__ = CLASS_ROUTINE_DOCSTRING.format(model=model.__name__)

