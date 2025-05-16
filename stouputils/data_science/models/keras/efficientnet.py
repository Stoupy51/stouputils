""" EfficientNetV2 models implementation.

This module provides wrapper classes for the EfficientNetV2 family of models from the Keras applications.
EfficientNetV2 models are a family of convolutional neural networks that achieve better
parameter efficiency and faster training speed compared to prior models.

Available models:

- EfficientNetV2M: Medium-sized variant balancing performance and computational cost
- EfficientNetV2L: Large variant with higher capacity for complex tasks

All models support transfer learning from ImageNet pre-trained weights.
"""
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
from __future__ import annotations

from keras.models import Model
from keras.src.applications.efficientnet import EfficientNetB0 as EfficientNetB0_keras
from keras.src.applications.efficientnet_v2 import EfficientNetV2B0 as EfficientNetV2B0_keras
from keras.src.applications.efficientnet_v2 import EfficientNetV2L as EfficientNetV2L_keras
from keras.src.applications.efficientnet_v2 import EfficientNetV2M as EfficientNetV2M_keras
from keras.src.applications.efficientnet_v2 import EfficientNetV2S as EfficientNetV2S_keras

from ....decorators import simple_cache
from ..base_keras import BaseKeras
from ..model_interface import CLASS_ROUTINE_DOCSTRING, MODEL_DOCSTRING


# Classes
class EfficientNetV2M(BaseKeras):
	def _get_base_model(self) -> Model:
		return EfficientNetV2M_keras(include_top=False, classes=self.num_classes)

class EfficientNetV2L(BaseKeras):
	def _get_base_model(self) -> Model:
		return EfficientNetV2L_keras(include_top=False, classes=self.num_classes)

class EfficientNetV2B0(BaseKeras):
	def _get_base_model(self) -> Model:
		return EfficientNetV2B0_keras(include_top=False, classes=self.num_classes)

class EfficientNetV2S(BaseKeras):
	def _get_base_model(self) -> Model:
		return EfficientNetV2S_keras(include_top=False, classes=self.num_classes)

# Classes for original EfficientNet models
class EfficientNetB0(BaseKeras):
	def _get_base_model(self) -> Model:
		return EfficientNetB0_keras(include_top=False, classes=self.num_classes)


# Docstrings
for model in [EfficientNetV2M, EfficientNetV2L, EfficientNetV2B0, EfficientNetV2S, EfficientNetB0]:
	model.__doc__ = MODEL_DOCSTRING.format(model=model.__name__)
	model.class_routine = simple_cache(model.class_routine)
	model.class_routine.__doc__ = CLASS_ROUTINE_DOCSTRING.format(model=model.__name__)

