""" ResNet models implementation.

This module provides wrapper classes for the ResNet family of models from the Keras applications.
It includes both ResNetV2 models with pre-activation residual blocks and ResNetRS
(ResNet with Revisited Scaling) models that offer improved performance
through various scaling techniques.

Available models:

- ResNetV2 family: Improved ResNet architectures with pre-activation blocks
    - ResNet50V2
    - ResNet101V2
    - ResNet152V2

All models support transfer learning from ImageNet pre-trained weights.
"""
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
from __future__ import annotations

from keras.models import Model
from keras.src.applications.resnet_v2 import ResNet50V2 as ResNet50V2_keras
from keras.src.applications.resnet_v2 import ResNet101V2 as ResNet101V2_keras
from keras.src.applications.resnet_v2 import ResNet152V2 as ResNet152V2_keras

from ....decorators import simple_cache
from ..base_keras import BaseKeras
from ..model_interface import CLASS_ROUTINE_DOCSTRING, MODEL_DOCSTRING


# Classes
class ResNet50V2(BaseKeras):
	def _get_base_model(self) -> Model:
		return ResNet50V2_keras(include_top=False, classes=self.num_classes)

class ResNet101V2(BaseKeras):
	def _get_base_model(self) -> Model:
		return ResNet101V2_keras(include_top=False, classes=self.num_classes)

class ResNet152V2(BaseKeras):
	def _get_base_model(self) -> Model:
		return ResNet152V2_keras(include_top=False, classes=self.num_classes)


# Docstrings
for model in [ResNet50V2, ResNet101V2, ResNet152V2]:
	model.__doc__ = MODEL_DOCSTRING.format(model=model.__name__)
	model.class_routine = simple_cache(model.class_routine)
	model.class_routine.__doc__ = CLASS_ROUTINE_DOCSTRING.format(model=model.__name__)

