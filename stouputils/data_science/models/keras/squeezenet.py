""" SqueezeNet model implementation.

This module provides a wrapper class for the SqueezeNet model, a lightweight CNN architecture
that achieves AlexNet-level accuracy with 50x fewer parameters and a model size of less than 0.5MB.
SqueezeNet uses "fire modules" consisting of a squeeze layer with 1x1 filters followed by an
expand layer with a mix of 1x1 and 3x3 convolution filters.

Available models:
- SqueezeNet: Compact model with excellent performance-to-parameter ratio

The model supports transfer learning from ImageNet pre-trained weights.
"""
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
from __future__ import annotations

from typing import Any

from keras import backend
from keras.layers import (
	Activation,
	Convolution2D,
	Dropout,
	GlobalAveragePooling2D,
	GlobalMaxPooling2D,
	Input,
	MaxPooling2D,
	concatenate,
)
from keras.models import Model
from keras.utils import get_file, get_source_inputs

from ....decorators import simple_cache
from ..base_keras import BaseKeras
from ..model_interface import CLASS_ROUTINE_DOCSTRING, MODEL_DOCSTRING

# Constants
SQ1X1: str = "squeeze1x1"

WEIGHTS_PATH = "https://github.com/rcmalli/keras-squeezenet/releases/download/v1.0/squeezenet_weights_tf_dim_ordering_tf_kernels.h5"
WEIGHTS_PATH_NO_TOP = "https://github.com/rcmalli/keras-squeezenet/releases/download/v1.0/squeezenet_weights_tf_dim_ordering_tf_kernels_notop.h5"


# Modular function for Fire Node
def fire_module(x: Any, fire_id: int, squeeze: int = 16, expand: int = 64):
	""" Create a fire module with specified parameters.

	Args:
		x           (Tensor):         Input tensor
		fire_id     (int):            ID for the fire module
		squeeze     (int):            Number of filters for squeeze layer
		expand      (int):            Number of filters for expand layers

	Returns:
		Tensor:                Output tensor from the fire module
	"""
	s_id: str = f"fire{fire_id}"

	if backend.image_data_format() == "channels_first":
		channel_axis: int = 1
	else:
		channel_axis: int = 3

	x = Convolution2D(squeeze, (1, 1), padding="valid", name=f"{s_id}/squeeze1x1")(x)
	x = Activation("relu", name=f"{s_id}/relu_squeeze1x1")(x)

	left = Convolution2D(expand, (1, 1), padding="valid", name=f"{s_id}/expand1x1")(x)
	left = Activation("relu", name=f"{s_id}/relu_expand1x1")(left)

	right = Convolution2D(expand, (3, 3), padding="same", name=f"{s_id}/expand3x3")(x)
	right = Activation("relu", name=f"{s_id}/relu_expand3x3")(right)

	x = concatenate([left, right], axis=channel_axis, name=f"{s_id}/concat")
	return x


# Original SqueezeNet from paper
def SqueezeNet_keras(  # noqa: N802
	include_top: bool = True,
	weights: str = "imagenet",
	input_tensor: Any = None,
	input_shape: tuple[Any, ...] | None = None,
	pooling: str | None = None,
	classes: int = 1000
) -> Model:
	""" Instantiates the SqueezeNet architecture.

	Args:
		include_top            (bool):           Whether to include the fully-connected layer at the top
		weights                (str):            One of `None` or 'imagenet'
		input_tensor           (Tensor):         Optional Keras tensor as input
		input_shape            (tuple):          Optional shape tuple
		pooling                (str):            Optional pooling mode for feature extraction
		classes                (int):            Number of classes to classify images into

	Returns:
		Model:                 A Keras model instance
	"""

	if weights not in {'imagenet', None}:
		raise ValueError(
			"The `weights` argument should be either `None` (random initialization) "
			"or `imagenet` (pre-training on ImageNet)."
		)

	if include_top and weights == 'imagenet' and classes != 1000:
		raise ValueError(
			"If using `weights` as imagenet with `include_top` as true, `classes` should be 1000"
		)

	# Manually handle input shape logic instead of _obtain_input_shape
	default_size: int = 227
	min_size: int = 48
	if backend.image_data_format() == 'channels_first':
		default_shape: tuple[int, int, int] = (3, default_size, default_size)
		if weights == 'imagenet' and include_top and input_shape is not None and input_shape[0] != 3:
			raise ValueError(
				"When specifying `input_shape` and loading 'imagenet' weights, 'channels_first' input_shape "
				"should be (3, H, W)."
			)
	else: # channels_last
		default_shape = (default_size, default_size, 3)
		if weights == 'imagenet' and include_top and input_shape is not None and input_shape[2] != 3:
			raise ValueError(
				"When specifying `input_shape` and loading 'imagenet' weights, 'channels_last' input_shape "
				"should be (H, W, 3)."
			)

	if input_shape is None:
		input_shape = default_shape
	else:
		# Basic validation
		if len(input_shape) != 3:
			raise ValueError("`input_shape` must be a tuple of three integers.")
		if backend.image_data_format() == 'channels_first':
			if input_shape[1] is not None and input_shape[1] < min_size:
				raise ValueError(f"Input size must be at least {min_size}x{min_size}, got `input_shape=`{input_shape}")
			if input_shape[2] is not None and input_shape[2] < min_size:
				raise ValueError(f"Input size must be at least {min_size}x{min_size}, got `input_shape=`{input_shape}")
		else: # channels_last
			if input_shape[0] is not None and input_shape[0] < min_size:
				raise ValueError(f"Input size must be at least {min_size}x{min_size}, got `input_shape=`{input_shape}")
			if input_shape[1] is not None and input_shape[1] < min_size:
				raise ValueError(f"Input size must be at least {min_size}x{min_size}, got `input_shape=`{input_shape}")

	# Handle input tensor
	if input_tensor is None:
		img_input = Input(shape=input_shape)
	else:
		if not backend.is_keras_tensor(input_tensor):
			img_input = Input(tensor=input_tensor, shape=input_shape)
		else:
			img_input = input_tensor

	x = Convolution2D(64, (3, 3), strides=(2, 2), padding='valid', name='conv1')(img_input)
	x = Activation('relu', name='relu_conv1')(x)
	x = MaxPooling2D(pool_size=(3, 3), strides=(2, 2), name='pool1')(x)

	x = fire_module(x, fire_id=2, squeeze=16, expand=64)
	x = fire_module(x, fire_id=3, squeeze=16, expand=64)
	x = MaxPooling2D(pool_size=(3, 3), strides=(2, 2), name='pool3')(x)

	x = fire_module(x, fire_id=4, squeeze=32, expand=128)
	x = fire_module(x, fire_id=5, squeeze=32, expand=128)
	x = MaxPooling2D(pool_size=(3, 3), strides=(2, 2), name='pool5')(x)

	x = fire_module(x, fire_id=6, squeeze=48, expand=192)
	x = fire_module(x, fire_id=7, squeeze=48, expand=192)
	x = fire_module(x, fire_id=8, squeeze=64, expand=256)
	x = fire_module(x, fire_id=9, squeeze=64, expand=256)

	if include_top:
		# It's not obvious where to cut the network...
		# Could do the 8th or 9th layer... some work recommends cutting earlier layers.

		x = Dropout(0.5, name='drop9')(x)

		x = Convolution2D(classes, (1, 1), padding='valid', name='conv10')(x)
		x = Activation('relu', name='relu_conv10')(x)
		x = GlobalAveragePooling2D()(x)
		x = Activation('softmax', name='loss')(x)
	else:
		if pooling == 'avg':
			x = GlobalAveragePooling2D()(x)
		elif pooling == 'max':
			x = GlobalMaxPooling2D()(x)
		elif pooling is None:
			pass
		else:
			raise ValueError("Unknown argument for 'pooling'=" + pooling)

	# Ensure that the model takes into account
	# any potential predecessors of `input_tensor`.
	if input_tensor is not None:
		inputs = get_source_inputs(input_tensor)
	else:
		inputs = img_input

	model = Model(inputs, x, name='squeezenet')

	# load weights
	if weights == 'imagenet':
		if include_top:
			weights_path = get_file('squeezenet_weights_tf_dim_ordering_tf_kernels.h5',
									WEIGHTS_PATH,
									cache_subdir='models')
		else:
			weights_path = get_file('squeezenet_weights_tf_dim_ordering_tf_kernels_notop.h5',
									WEIGHTS_PATH_NO_TOP,
									cache_subdir='models')

		model.load_weights(weights_path)
	return model


# Classes
class SqueezeNet(BaseKeras):
	def _get_base_model(self) -> Model:
		return SqueezeNet_keras(
			include_top=False, classes=self.num_classes, input_shape=(224, 224, 3)
		)


# Docstrings
for model in [SqueezeNet]:
	model.__doc__ = MODEL_DOCSTRING.format(model=model.__name__)
	model.class_routine = simple_cache(model.class_routine)
	model.class_routine.__doc__ = CLASS_ROUTINE_DOCSTRING.format(model=model.__name__)

