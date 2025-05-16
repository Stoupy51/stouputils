""" DenseNet models implementation.

This module provides wrapper classes for the DenseNet family of models from the Keras applications.
DenseNet models utilize dense connections between layers, where each layer obtains additional inputs
from all preceding layers and passes on its feature-maps to all subsequent layers.

Available models:

- DenseNet121: Smallest variant with 121 layers
- DenseNet169: Medium-sized variant with 169 layers
- DenseNet201: Largest variant with 201 layers

All models support transfer learning from ImageNet pre-trained weights.
"""
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
from __future__ import annotations

from keras.models import Model
from keras.src.applications.densenet import DenseNet121 as DenseNet121_keras
from keras.src.applications.densenet import DenseNet169 as DenseNet169_keras
from keras.src.applications.densenet import DenseNet201 as DenseNet201_keras

from ....decorators import simple_cache
from ..base_keras import BaseKeras
from ..model_interface import CLASS_ROUTINE_DOCSTRING, MODEL_DOCSTRING


# Classes
class DenseNet121(BaseKeras):
	def _get_base_model(self) -> Model:
		return DenseNet121_keras(include_top=False, classes=self.num_classes)

class DenseNet169(BaseKeras):
	def _get_base_model(self) -> Model:
		return DenseNet169_keras(include_top=False, classes=self.num_classes)

class DenseNet201(BaseKeras):
	def _get_base_model(self) -> Model:
		return DenseNet201_keras(include_top=False, classes=self.num_classes)


# Docstrings
for model in [DenseNet121, DenseNet169, DenseNet201]:
	model.__doc__ = MODEL_DOCSTRING.format(model=model.__name__)
	model.class_routine = simple_cache(model.class_routine)
	model.class_routine.__doc__ = CLASS_ROUTINE_DOCSTRING.format(model=model.__name__)

