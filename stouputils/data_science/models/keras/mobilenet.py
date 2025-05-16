""" MobileNet models implementation.

This module provides wrapper classes for the MobileNet family of models from the Keras applications.
MobileNet models are designed for mobile and embedded vision applications,
offering efficient architectures that deliver high accuracy with low computational requirements.

Available models:

- MobileNet: Original MobileNet architecture using depthwise separable convolutions
- MobileNetV2: Lightweight architecture using inverted residuals and linear bottlenecks
- MobileNetV3Small: Compact variant of MobileNetV3 optimized for mobile devices
- MobileNetV3Large: Larger variant of MobileNetV3 with higher capacity

All models support transfer learning from ImageNet pre-trained weights.
"""
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
from __future__ import annotations

from keras.models import Model
from keras.src.applications.mobilenet import MobileNet as MobileNet_keras
from keras.src.applications.mobilenet_v2 import MobileNetV2 as MobileNetV2_keras
from keras.src.applications.mobilenet_v3 import MobileNetV3Large as MobileNetV3Large_keras
from keras.src.applications.mobilenet_v3 import MobileNetV3Small as MobileNetV3Small_keras

from ....decorators import simple_cache
from ..base_keras import BaseKeras
from ..model_interface import CLASS_ROUTINE_DOCSTRING, MODEL_DOCSTRING


# Classes
class MobileNet(BaseKeras):
	def _get_base_model(self) -> Model:
		return MobileNet_keras(include_top=False, classes=self.num_classes)

class MobileNetV2(BaseKeras):
	def _get_base_model(self) -> Model:
		return MobileNetV2_keras(include_top=False, classes=self.num_classes)

class MobileNetV3Small(BaseKeras):
	def _get_base_model(self) -> Model:
		return MobileNetV3Small_keras(include_top=False, classes=self.num_classes)

class MobileNetV3Large(BaseKeras):
	def _get_base_model(self) -> Model:
		return MobileNetV3Large_keras(include_top=False, classes=self.num_classes)


# Docstrings
for model in [MobileNet, MobileNetV2, MobileNetV3Small, MobileNetV3Large]:
	model.__doc__ = MODEL_DOCSTRING.format(model=model.__name__)
	model.class_routine = simple_cache(model.class_routine)
	model.class_routine.__doc__ = CLASS_ROUTINE_DOCSTRING.format(model=model.__name__)

