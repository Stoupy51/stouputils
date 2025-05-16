""" ConvNeXt models implementation.

This module provides wrapper classes for the ConvNeXt family of models from the Keras applications.
ConvNeXt models are a family of pure convolutional networks that match or outperform
Vision Transformers (ViTs) while maintaining the simplicity and efficiency of CNNs.

Available models:

- ConvNeXtTiny: Smallest variant with fewer parameters for resource-constrained environments
- ConvNeXtSmall: Compact model balancing performance and size
- ConvNeXtBase: Standard model with good performance for general use cases
- ConvNeXtLarge: Larger model with higher capacity for complex tasks
- ConvNeXtXLarge: Largest variant with maximum capacity for demanding applications

All models support transfer learning from ImageNet pre-trained weights.
"""
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
from __future__ import annotations

from keras.models import Model
from keras.src.applications.convnext import ConvNeXtBase as ConvNeXtBase_keras
from keras.src.applications.convnext import ConvNeXtLarge as ConvNeXtLarge_keras
from keras.src.applications.convnext import ConvNeXtSmall as ConvNeXtSmall_keras
from keras.src.applications.convnext import ConvNeXtTiny as ConvNeXtTiny_keras
from keras.src.applications.convnext import ConvNeXtXLarge as ConvNeXtXLarge_keras

from ....decorators import simple_cache
from ..base_keras import BaseKeras
from ..model_interface import CLASS_ROUTINE_DOCSTRING, MODEL_DOCSTRING


# Classes
class ConvNeXtTiny(BaseKeras):
	def _get_base_model(self) -> Model:
		return ConvNeXtTiny_keras(include_top=False, classes=self.num_classes)

class ConvNeXtSmall(BaseKeras):
	def _get_base_model(self) -> Model:
		return ConvNeXtSmall_keras(include_top=False, classes=self.num_classes)

class ConvNeXtBase(BaseKeras):
	def _get_base_model(self) -> Model:
		return ConvNeXtBase_keras(include_top=False, classes=self.num_classes)

class ConvNeXtLarge(BaseKeras):
	def _get_base_model(self) -> Model:
		return ConvNeXtLarge_keras(include_top=False, classes=self.num_classes)

class ConvNeXtXLarge(BaseKeras):
	def _get_base_model(self) -> Model:
		return ConvNeXtXLarge_keras(include_top=False, classes=self.num_classes)


# Docstrings
for model in [ConvNeXtTiny, ConvNeXtSmall, ConvNeXtBase, ConvNeXtLarge, ConvNeXtXLarge]:
	model.__doc__ = MODEL_DOCSTRING.format(model=model.__name__)
	model.class_routine = simple_cache(model.class_routine)
	model.class_routine.__doc__ = CLASS_ROUTINE_DOCSTRING.format(model=model.__name__)

