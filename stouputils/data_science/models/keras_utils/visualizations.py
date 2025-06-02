""" Keras utilities for generating Grad-CAM heatmaps and saliency maps for model interpretability. """

# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportMissingTypeStubs=false
# pyright: reportIndexIssue=false

# Imports
import os
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from keras.models import Model
from matplotlib.colors import Colormap
from numpy.typing import NDArray
from PIL import Image

from ....decorators import handle_error
from ....print import error, warning
from ...config.get import DataScienceConfig


@handle_error(error_log=DataScienceConfig.ERROR_LOG)
def make_gradcam_heatmap(
	model: Model,
	img: NDArray[Any],
	class_idx: int = 0,
	last_conv_layer_name: str = "",
	one_per_channel: bool = False
) -> list[NDArray[Any]]:
	""" Generate a Grad-CAM heatmap for a given image and model.

	Args:
		model                 (Model):       The pre-trained TensorFlow model
		img                   (NDArray[Any]):  The preprocessed image array (ndim=3 or 4 with shape=(1, ?, ?, ?))
		class_idx             (int):         The class index to use for the Grad-CAM heatmap
		last_conv_layer_name  (str):         Name of the last convolutional layer in the model
			(optional, will try to find it automatically)
		one_per_channel       (bool):        If True, return one heatmap per channel
	Returns:
		list[NDArray[Any]]: The Grad-CAM heatmap(s)

	Examples:
		.. code-block:: python

			> model: Model = ...
			> img: NDArray[Any] = np.array(Image.open("path/to/image.jpg").convert("RGB"))
			> last_conv_layer: str = Utils.find_last_conv_layer(model) or "conv5_block3_out"
			> heatmap: NDArray[Any] = Utils.make_gradcam_heatmap(model, img, last_conv_layer)[0]
			> Image.fromarray(heatmap).save("heatmap.png")
	"""
	# Assertions
	assert isinstance(model, Model), "Model must be a valid Keras model"
	assert isinstance(img, np.ndarray), "Image array must be a valid numpy array"

	# If img is not a batch of 1, convert it to a batch of 1
	if img.ndim == 3:
		img = np.expand_dims(img, axis=0)
	assert img.ndim == 4 and img.shape[0] == 1, "Image array must be a batch of 1 (shape=(1, ?, ?, ?))"

	# If last_conv_layer_name is not provided, find it automatically
	if not last_conv_layer_name:
		last_conv_layer_name = find_last_conv_layer(model)
		if not last_conv_layer_name:
			error("Last convolutional layer not found. Please provide the name of the last convolutional layer.")

	# Get the last convolutional layer
	last_layer: list[Model] | Any = model.get_layer(last_conv_layer_name)
	if isinstance(last_layer, list):
		last_layer = last_layer[0]

	# Create a model that outputs both the last conv layer's activations and predictions
	grad_model: Model = Model(
		[model.inputs],
		[last_layer.output, model.output]
	)

	# Record operations for automatic differentiation using GradientTape.
	with tf.GradientTape() as tape:

		# Forward pass: get the activations of the last conv layer and the predictions.
		conv_outputs: tf.Tensor
		predictions: tf.Tensor
		conv_outputs, predictions = grad_model(img) # pyright: ignore [reportGeneralTypeIssues]
		# print("conv_outputs shape:", conv_outputs.shape)
		# print("predictions shape:", predictions.shape)

		# Compute the loss with respect to the positive class
		loss: tf.Tensor = predictions[:, class_idx]

		# Compute the gradient of the loss with respect to the activations ..
		# .. of the last conv layer
		grads: tf.Tensor = tf.convert_to_tensor(tape.gradient(loss, conv_outputs))
		# print("grads shape:", grads.shape)

	# Initialize heatmaps list
	heatmaps: list[NDArray[Any]] = []

	if one_per_channel:
		# Return one heatmap per channel
		# Get the number of filters in the last conv layer
		num_filters: int = int(tf.shape(conv_outputs)[-1])

		for i in range(num_filters):
			# Compute the mean intensity of the gradients for this filter
			pooled_grad: tf.Tensor = tf.reduce_mean(grads[:, :, :, i])

			# Get the activation map for this filter
			activation_map: tf.Tensor = conv_outputs[:, :, :, i]

			# Weight the activation map by the gradient
			weighted_map: tf.Tensor = activation_map * pooled_grad # pyright: ignore [reportOperatorIssue]

			# Ensure that the heatmap has non-negative values and normalize it
			heatmap: tf.Tensor = tf.maximum(weighted_map, 0) / tf.math.reduce_max(weighted_map)

			# Remove possible dims of size 1 + convert the heatmap to a numpy array
			heatmaps.append(tf.squeeze(heatmap).numpy())
	else:
		# Compute the mean intensity of the gradients for each filter in the last conv layer.
		pooled_grads: tf.Tensor = tf.reduce_mean(grads, axis=(0, 1, 2))

		# Multiply each activation map in the last conv layer by the corresponding
		# gradient average, which emphasizes the parts of the image that are important.
		heatmap: tf.Tensor = conv_outputs @ tf.expand_dims(pooled_grads, axis=-1)
		# print("heatmap shape (before squeeze):", heatmap.shape)

		# Ensure that the heatmap has non-negative values and normalize it.
		heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)

		# Remove possible dims of size 1 + convert the heatmap to a numpy array.
		heatmaps.append(tf.squeeze(heatmap).numpy())

	return heatmaps

@handle_error(error_log=DataScienceConfig.ERROR_LOG)
def make_saliency_map(
	model: Model,
	img: NDArray[Any],
	class_idx: int = 0,
	one_per_channel: bool = False
) -> list[NDArray[Any]]:
	""" Generate a saliency map for a given image and model.

	A saliency map shows which pixels in the input image have the greatest influence on the
	model's prediction.

	Args:
		model            (Model):       The pre-trained TensorFlow model
		img              (NDArray[Any]):  The preprocessed image array (batch of 1)
		class_idx        (int):         The class index to use for the saliency map
		one_per_channel  (bool):        If True, return one saliency map per channel
	Returns:
		list[NDArray[Any]]: The saliency map(s) normalized to range [0,1]

	Examples:
		.. code-block:: python

			> model: Model = ...
			> img: NDArray[Any] = np.array(Image.open("path/to/image.jpg").convert("RGB"))
			> saliency: NDArray[Any] = Utils.make_saliency_map(model, img)[0]
	"""
	# Assertions
	assert isinstance(model, Model), "Model must be a valid Keras model"
	assert isinstance(img, np.ndarray), "Image array must be a valid numpy array"

	# If img is not a batch of 1, convert it to a batch of 1
	if img.ndim == 3:
		img = np.expand_dims(img, axis=0)
	assert img.ndim == 4 and img.shape[0] == 1, "Image array must be a batch of 1 (shape=(1, ?, ?, ?))"

	# Convert the numpy array to a tensor
	img_tensor = tf.convert_to_tensor(img, dtype=tf.float32)

	# Record operations for automatic differentiation
	with tf.GradientTape() as tape:
		tape.watch(img_tensor)
		predictions: tf.Tensor = model(img_tensor) # pyright: ignore [reportAssignmentType]
		# Use class index for positive class prediction
		loss: tf.Tensor = predictions[:, class_idx]

	# Compute gradients of loss with respect to input image
	try:
		grads = tape.gradient(loss, img_tensor)
		# Cast to tensor to satisfy type checker
		grads = tf.convert_to_tensor(grads)
	except Exception as e:
		warning(f"Error computing gradients: {e}")
		return []

	# Initialize saliency maps list
	saliency_maps: list[NDArray[Any]] = []

	if one_per_channel:
		# Return one saliency map per channel
		# Get the last dimension size as an integer
		num_channels: int = int(tf.shape(grads)[-1])
		for i in range(num_channels):
			# Extract gradients for this channel
			channel_grads: tf.Tensor = tf.abs(grads[:, :, :, i])

			# Apply smoothing to make the map more visually coherent
			channel_grads = tf.nn.avg_pool2d(
				tf.expand_dims(channel_grads, -1),
				ksize=3, strides=1, padding='SAME'
			)
			channel_grads = tf.squeeze(channel_grads)

			# Normalize the saliency map for this channel
			channel_max = tf.math.reduce_max(channel_grads)
			if channel_max > 0:
				channel_saliency: tf.Tensor = channel_grads / channel_max
			else:
				channel_saliency: tf.Tensor = channel_grads

			saliency_maps.append(channel_saliency.numpy().squeeze()) # type: ignore
	else:
		# Take absolute value of gradients
		abs_grads = tf.abs(grads)

		# Sum across color channels for RGB images
		saliency = tf.reduce_sum(abs_grads, axis=-1)

		# Apply smoothing to make the map more visually coherent
		saliency = tf.nn.avg_pool2d(
			tf.expand_dims(saliency, -1),
			ksize=3, strides=1, padding='SAME'
		)
		saliency = tf.squeeze(saliency)

		# Normalize saliency map
		saliency_max = tf.math.reduce_max(saliency)
		if saliency_max > 0:
			saliency = saliency / saliency_max

		saliency_maps.append(saliency.numpy().squeeze())

	return saliency_maps

@handle_error(error_log=DataScienceConfig.ERROR_LOG)
def find_last_conv_layer(model: Model) -> str:
	""" Find the name of the last convolutional layer in a model.

	Args:
		model (Model): The TensorFlow model to analyze
	Returns:
		str: Name of the last convolutional layer if found, otherwise an empty string

	Examples:
		.. code-block:: python

			> model: Model = ...
			> last_conv_layer: str = Utils.find_last_conv_layer(model)
			> print(last_conv_layer)
			'conv5_block3_out'
	"""
	assert isinstance(model, Model), "Model must be a valid Keras model"

	# Find the last convolutional layer by iterating through the layers in reverse
	last_conv_layer_name: str = ""
	for layer in reversed(model.layers):
		if isinstance(layer, tf.keras.layers.Conv2D):
			last_conv_layer_name = layer.name
			break

	# Return the name of the last convolutional layer
	return last_conv_layer_name

@handle_error(error_log=DataScienceConfig.ERROR_LOG)
def create_visualization_overlay(
	original_img: NDArray[Any] | Image.Image,
	heatmap: NDArray[Any],
	alpha: float = 0.4,
	colormap: str = "jet"
) -> NDArray[Any]:
	""" Create an overlay of the original image with a heatmap visualization.

	Args:
		original_img  (NDArray[Any] | Image.Image):  The original image array or PIL Image
		heatmap       (NDArray[Any]):                The heatmap to overlay (normalized to 0-1)
		alpha         (float):                     Transparency level of overlay (0-1)
		colormap      (str):                       Matplotlib colormap to use for heatmap
	Returns:
		NDArray[Any]: The overlaid image

	Examples:
		.. code-block:: python

			> original: NDArray[Any] | Image.Image = ...
			> heatmap: NDArray[Any] = Utils.make_gradcam_heatmap(model, img)[0]
			> overlay: NDArray[Any] = Utils.create_visualization_overlay(original, heatmap)
			> Image.fromarray(overlay).save("overlay.png")
	"""
	# Ensure heatmap is normalized to 0-1
	if heatmap.max() > 0:
		heatmap = heatmap / heatmap.max()

	## Apply colormap to heatmap
	# Get the colormap
	cmap: Colormap = plt.cm.get_cmap(colormap)

	# Ensure heatmap is at least 2D to prevent tuple return from cmap
	if np.isscalar(heatmap) or heatmap.ndim == 0:
		heatmap = np.array([[heatmap]])

	# Apply colormap and ensure it's a numpy array
	heatmap_rgb: NDArray[Any] = np.array(cmap(heatmap))

	# Remove alpha channel if present
	if heatmap_rgb.ndim >= 3:
		heatmap_rgb = heatmap_rgb[:, :, :3]

	heatmap_rgb = (255 * heatmap_rgb).astype(np.uint8)

	# Convert original image to PIL Image if it's a numpy array
	if isinstance(original_img, np.ndarray):
		# Scale to 0-255 range if image is normalized (0-1)
		if original_img.max() <= 1:
			img: NDArray[Any] = (original_img * 255).astype(np.uint8)
		else:
			img: NDArray[Any] = original_img.astype(np.uint8)
		original_pil: Image.Image = Image.fromarray(img)
	else:
		original_pil: Image.Image = original_img

	# Force RGB mode
	if original_pil.mode != "RGB":
		original_pil = original_pil.convert("RGB")

	# Convert heatmap to PIL Image
	heatmap_pil: Image.Image = Image.fromarray(heatmap_rgb)

	# Resize heatmap to match original image size if needed
	if heatmap_pil.size != original_pil.size:
		heatmap_pil = heatmap_pil.resize(original_pil.size, Image.Resampling.LANCZOS)

	# Ensure heatmap is also in RGB mode
	if heatmap_pil.mode != "RGB":
		heatmap_pil = heatmap_pil.convert("RGB")

	# Blend images
	overlaid_img: Image.Image = Image.blend(original_pil, heatmap_pil, alpha=alpha)

	return np.array(overlaid_img)

@handle_error(error_log=DataScienceConfig.ERROR_LOG)
def all_visualizations_for_image(
	model: Model,
	folder_path: str,
	img: NDArray[Any],
	base_name: str,
	class_idx: int,
	class_name: str,
	files: tuple[str, ...],
	data_type: str
) -> None:
	""" Process a single image to generate visualizations and determine prediction correctness.

	Args:
		model          (Model):           The pre-trained TensorFlow model
		folder_path    (str):             The path to the folder where the visualizations will be saved
		img            (NDArray[Any]):    The preprocessed image array (batch of 1)
		base_name      (str):             The base name of the image
		class_idx      (int):             The **true** class index for the image
		class_name     (str):             The **true** class name for organizing folders
		files          (tuple[str, ...]): List of original file paths for the subject
		data_type      (str):             Type of data ("test" or "train")
	"""
	# Set directories based on data type
	saliency_dir: str = f"{folder_path}/{data_type}/saliency_maps"
	grad_cam_dir: str = f"{folder_path}/{data_type}/grad_cams"

	# Convert label to class name and load all original images
	original_imgs: list[Image.Image] = [Image.open(f).convert("RGB") for f in files]

	# Find the maximum dimensions across all images
	max_shape: tuple[int, int] = max(i.size for i in original_imgs)

	# Resize all images to match the largest dimensions while preserving aspect ratio
	resized_imgs: list[NDArray[Any]] = []
	for original_img in original_imgs:
		if original_img.size != max_shape:
			original_img = original_img.resize(max_shape, resample=Image.Resampling.LANCZOS)
		resized_imgs.append(np.array(original_img))

	# Take mean of resized images
	subject_image: NDArray[Any] = np.mean(np.stack(resized_imgs), axis=0).astype(np.uint8)

	# Perform prediction to determine correctness
	# Ensure img is in batch format (add dimension if needed)
	img_batch: NDArray[Any] = np.expand_dims(img, axis=0) if img.ndim == 3 else img
	predicted_class_idx: int = int(np.argmax(model.predict(img_batch, verbose=0)[0])) # type: ignore
	prediction_correct: bool = (predicted_class_idx == class_idx)
	status_suffix: str = "_correct" if prediction_correct else "_missed"

	# Create and save Grad-CAM visualization
	heatmap: NDArray[Any] = make_gradcam_heatmap(model, img, class_idx=class_idx, one_per_channel=False)[0]
	overlay: NDArray[Any] = create_visualization_overlay(subject_image, heatmap)

	# Save the overlay visualization with status suffix
	grad_cam_path = f"{grad_cam_dir}/{class_name}/{base_name}{status_suffix}_gradcam.png"
	os.makedirs(os.path.dirname(grad_cam_path), exist_ok=True)
	Image.fromarray(overlay).save(grad_cam_path)

	# Create and save saliency maps
	saliency_map: NDArray[Any] = make_saliency_map(model, img, class_idx=class_idx, one_per_channel=False)[0]
	overlay: NDArray[Any] = create_visualization_overlay(subject_image, saliency_map)

	# Save the overlay visualization with status suffix
	saliency_path = f"{saliency_dir}/{class_name}/{base_name}{status_suffix}_saliency.png"
	os.makedirs(os.path.dirname(saliency_path), exist_ok=True)
	Image.fromarray(overlay).save(saliency_path)

