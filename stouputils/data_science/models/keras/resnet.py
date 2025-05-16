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
- ResNetRS family: ResNet models with revisited scaling for better efficiency
    - ResNetRS50
    - ResNetRS101
    - ResNetRS152
    - ResNetRS200
    - ResNetRS270
    - ResNetRS350
    - ResNetRS420

All models support transfer learning from ImageNet pre-trained weights.
"""
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
from __future__ import annotations

from keras.models import Model
from keras.src.applications.resnet_rs import ResNetRS50 as ResNetRS50_keras
from keras.src.applications.resnet_rs import ResNetRS101 as ResNetRS101_keras
from keras.src.applications.resnet_rs import ResNetRS152 as ResNetRS152_keras
from keras.src.applications.resnet_rs import ResNetRS200 as ResNetRS200_keras
from keras.src.applications.resnet_rs import ResNetRS270 as ResNetRS270_keras
from keras.src.applications.resnet_rs import ResNetRS350 as ResNetRS350_keras
from keras.src.applications.resnet_rs import ResNetRS420 as ResNetRS420_keras
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

class ResNetRS50(BaseKeras):
	def _get_base_model(self) -> Model:
		return ResNetRS50_keras(include_top=False, classes=self.num_classes)

class ResNetRS101(BaseKeras):
	def _get_base_model(self) -> Model:
		return ResNetRS101_keras(include_top=False, classes=self.num_classes)

class ResNetRS152(BaseKeras):
	def _get_base_model(self) -> Model:
		return ResNetRS152_keras(include_top=False, classes=self.num_classes)

class ResNetRS200(BaseKeras):
	def _get_base_model(self) -> Model:
		return ResNetRS200_keras(include_top=False, classes=self.num_classes)

class ResNetRS270(BaseKeras):
	def _get_base_model(self) -> Model:
		return ResNetRS270_keras(include_top=False, classes=self.num_classes)

class ResNetRS350(BaseKeras):
	def _get_base_model(self) -> Model:
		return ResNetRS350_keras(include_top=False, classes=self.num_classes)

class ResNetRS420(BaseKeras):
	def _get_base_model(self) -> Model:
		return ResNetRS420_keras(include_top=False, classes=self.num_classes)


# Docstrings
for model in [
	ResNet50V2, ResNet101V2, ResNet152V2,
	ResNetRS50, ResNetRS101, ResNetRS152, ResNetRS200,
	ResNetRS270, ResNetRS350, ResNetRS420
]:
	model.__doc__ = MODEL_DOCSTRING.format(model=model.__name__)
	model.class_routine = simple_cache(model.class_routine)
	model.class_routine.__doc__ = CLASS_ROUTINE_DOCSTRING.format(model=model.__name__)

