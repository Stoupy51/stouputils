
# pyright: reportIncompatibleMethodOverride=false

# Imports
from __future__ import annotations

import random
from collections.abc import Callable, Iterable
from enum import Enum
from typing import Any, Literal, NamedTuple

import cv2
from numpy.typing import NDArray
from PIL import Image

from ..range_tuple import RangeTuple

# Import folders
from .image import (
	adaptive_denoise_image,
	auto_contrast_image,
	bias_field_correction_image,
	bilateral_denoise_image,
	binary_threshold_image,
	blur_image,
	brightness_image,
	canny_image,
	clahe_image,
	contrast_image,
	curvature_flow_filter_image,
	flip_image,
	invert_image,
	laplacian_image,
	median_blur_image,
	nlm_denoise_image,
	noise_image,
	normalize_image,
	random_erase_image,
	resize_image,
	rotate_image,
	salt_pepper_image,
	sharpen_image,
	shear_image,
	threshold_image,
	translate_image,
	tv_denoise_image,
	wavelet_denoise_image,
	zoom_image,
)


# Tuple class
class ProcessingTechnique(NamedTuple):
	""" A named tuple containing an processing technique.

	The following descriptions are the recommendations:

	- rotation:			Rotation between -20° and +20° is generally safe
	- translation:		Translation up to 15% to avoid position bias
	- shearing:			Shearing up to 15° on x and y axes
	- noise:			Gaussian noise with fixed values [0.3,0.4,0.5]
	- salt-pepper:		Salt-pepper noise with densities [0.01,0.02,0.03]
	- sharpening:		Gaussian blur (variance=1) then subtract from original
	- contrast:			Linear scaling between min/max intensities [0.7,1.3]
	- axis_flip:		Flip along x and/or y axis (0 for x, 1 for y, 2 for both), probability=0.5
	- zoom:				Magnification/zoom between 85% and 115%
	- brightness:		Adjust overall image brightness [0.7,1.3]
	- blur:				Gaussian blur for reduced sharpness [0.5,2.0]
	- random_erase:		Randomly erase rectangles (1-10% of image) to learn descriptive features
	- clahe:			Contrast Limited Adaptive Histogram Equalization (clip_limit=[1.0,4.0], tile_size=8)
	- binary_threshold:	Binary thresholding with threshold [0.1,0.9]
	- threshold:		Multi-level thresholding with levels [0.3,0.6]
	- canny:            Canny edge detection (thresholds=[50/255,150/255], aperture=3)
	- laplacian:        Laplacian edge detection with 3x3 kernel
	- auto_contrast:    Auto contrast the image
	- bias_field_correction: Bias field correction
	- curvature_flow_filter: Curvature flow filter (time_step=0.05, iterations=5)
	- median_blur:      Median blur (kernel_size=15, iterations=10)
	- resize:			Resize the image (width=224, height=224, resample=Image.Resampling.LANCZOS)
	- normalize:        Normalize the image (min=0, max=255, method=cv2.NORM_MINMAX)
	- nlm_denoise:      Non-local means denoising (h=10, template_window_size=7, search_window_size=21)
	- bilateral_denoise: Bilateral filter denoising (d=9, sigma_color=75, sigma_space=75)
	- tv_denoise:       Total variation denoising (weight=0.1, iterations=30)
	- wavelet_denoise:  Wavelet denoising (wavelet='db1', mode='soft', wavelet_levels=3)
	- adaptive_denoise: Adaptive denoising (method="nlm", strength=0.5)
	- custom:			Custom processing technique (callable) # Ex: ProcessingTechnique("custom", custom=f)
	"""
	# The following descriptions are the recommendations
	name: Literal[
		"rotation", "translation", "shearing", "noise", "salt-pepper", "sharpening",
		"contrast", "axis_flip", "zoom", "brightness", "blur", "random_erase", "clahe",
		"binary_threshold", "threshold", "canny", "laplacian", "auto_contrast",
		"bias_field_correction", "curvature_flow_filter", "resize",
		"normalize", "median_blur", "nlm_denoise", "bilateral_denoise",
		"tv_denoise", "wavelet_denoise", "adaptive_denoise", "invert", "custom"
	]
	""" Name of the processing technique """
	ranges: list[Iterable[Any] | RangeTuple]
	""" List of ranges for the processing technique.
	Depending on the technique, multiple ranges might be needed.
	Ex: Translation (x and y axes) or Shearing (x and y axes). """
	probability: float = 1.0
	""" Probability of applying the processing technique (default: 1.0).
	Should be used on techniques like "axis_flip" or "random_erase"
	where the probability of applying the technique is not 100%. """
	custom: Callable[..., NDArray[Any]] | None = None
	""" Custom processing technique (callable), name must be "custom", e.g. ProcessingTechnique("custom", custom=f) """

	def __str__(self) -> str:
		return (
			f"name={self.name}, ranges={self.ranges}, probability={self.probability}, "
			f"custom={self.custom.__name__ if self.custom else None}"
		)

	def __repr__(self) -> str:
		return (
			f"ProcessingTechnique(name={self.name!r}, ranges={self.ranges!r}, "
			f"probability={self.probability}, custom={self.custom.__name__ if self.custom else None}"
		)

	def __mul__(self, other: float) -> ProcessingTechnique:
		""" Multiply all ranges by a scalar value.

		Args:
			other (float): Value to multiply ranges by
		Returns:
			ProcessingTechnique: New object with scaled ranges
		"""
		return ProcessingTechnique(
			self.name,
			[
				(r * other) if isinstance(r, RangeTuple) else [x * other if isinstance(x, float | int) else x for x in r]
				for r in self.ranges
			],
			probability=self.probability,
			custom=self.custom
		)

	def __truediv__(self, other: float) -> ProcessingTechnique:
		""" Divide all ranges by a scalar value.

		Args:
			other (float): Value to divide ranges by
		Returns:
			ProcessingTechnique: New object with scaled ranges
		"""
		return ProcessingTechnique(
			self.name,
			[
				(r / other) if isinstance(r, RangeTuple) else [x / other if isinstance(x, float | int) else x for x in r]
				for r in self.ranges
			],
			probability=self.probability,
			custom=self.custom
		)

	def deterministic(self, use_default: bool = False) -> ProcessingTechnique:
		""" Convert the RangeTuple to values by calling the RangeTuple.random() method. """
		# Make values deterministic
		values: list[Iterable[Any]] = []
		for range in self.ranges:
			if isinstance(range, RangeTuple):
				if use_default:
					values.append([range.default])
				else:
					values.append([range.random()])
			else:
				values.append(range)

		# Make probability deterministic (0 or 1)
		probability: float = 1.0 if random.random() < self.probability else 0.0
		return ProcessingTechnique(self.name, values, probability=probability, custom=self.custom)

	def apply(self, image: NDArray[Any], dividers: tuple[float, float] = (1.0, 1.0), times: int = 1) -> NDArray[Any]:
		""" Apply the processing technique to the image.

		Args:
			image     (NDArray[Any]):           Image to apply the processing technique to
			dividers  (tuple[float, float]):    Dividers used to adjust the processing technique parameters (default: (1.0, 1.0))
			times     (int):                    Number of times to apply the processing technique (default: 1)
		Returns:
			NDArray[Any]: Processed image
		"""
		assert not any(isinstance(x, RangeTuple) for x in self.ranges), (
			"All RangeTuples must be converted to values, "
			f"please call deterministic() before. {self.ranges=}"
		)

		# Check if the technique is applied
		if random.random() > self.probability:
			return image

		for _ in range(times):

			# Apply the processing technique
			if self.name == "rotation":
				angle: float = next(iter(self.ranges[0]))
				image = rotate_image(image, angle)

			elif self.name == "translation":
				x_shift: float = next(iter(self.ranges[0])) / dividers[0]
				y_shift: float = next(iter(self.ranges[1])) / dividers[1]
				image = translate_image(image, x_shift, y_shift)

			elif self.name == "shearing":
				x_shear: float = next(iter(self.ranges[0])) / dividers[0]
				y_shear: float = next(iter(self.ranges[1])) / dividers[1]
				image = shear_image(image, x_shear, y_shear)

			elif self.name == "axis_flip":
				axis: Literal["horizontal", "vertical", "both"] = next(iter(self.ranges[0]))
				image = flip_image(image, axis)

			elif self.name == "noise":
				intensity: float = next(iter(self.ranges[0]))
				image = noise_image(image, intensity)

			elif self.name == "salt-pepper":
				density: float = next(iter(self.ranges[0]))
				image = salt_pepper_image(image, density)

			elif self.name == "sharpening":
				alpha: float = next(iter(self.ranges[0]))
				image = sharpen_image(image, alpha)

			elif self.name == "contrast":
				factor: float = next(iter(self.ranges[0]))
				image = contrast_image(image, factor)

			elif self.name == "zoom":
				zoom_factor: float = next(iter(self.ranges[0])) / max(dividers)
				image = zoom_image(image, zoom_factor)

			elif self.name == "brightness":
				brightness_factor: float = next(iter(self.ranges[0]))
				image = brightness_image(image, brightness_factor)

			elif self.name == "blur":
				sigma: float = next(iter(self.ranges[0]))
				image = blur_image(image, sigma)

			elif self.name == "random_erase":
				ratio: float = next(iter(self.ranges[0])) / max(dividers)
				image = random_erase_image(image, ratio)

			elif self.name == "clahe":
				clip_limit: float = next(iter(self.ranges[0]))
				tile_grid_size: int = int(next(iter(self.ranges[0])))
				image = clahe_image(image, clip_limit, tile_grid_size)

			elif self.name == "binary_threshold":
				threshold: float = next(iter(self.ranges[0]))
				image = binary_threshold_image(image, threshold)

			elif self.name == "threshold":
				thresholds: list[float] = [next(iter(r)) for r in self.ranges]
				image = threshold_image(image, thresholds)

			elif self.name == "canny":
				threshold1: float = next(iter(self.ranges[0]))
				threshold2: float = next(iter(self.ranges[1]))
				aperture_size: int = int(next(iter(self.ranges[2]))) if len(self.ranges) > 2 else 3
				image = canny_image(image, threshold1, threshold2, aperture_size)

			elif self.name == "laplacian":
				kernel_size: int = int(next(iter(self.ranges[0]))) if self.ranges else 3
				image = laplacian_image(image, kernel_size)

			elif self.name == "auto_contrast":
				image = auto_contrast_image(image)

			elif self.name == "curvature_flow_filter":
				time_step: float = next(iter(self.ranges[0]))
				number_of_iterations: int = int(next(iter(self.ranges[1])))
				image = curvature_flow_filter_image(image, time_step, number_of_iterations)

			elif self.name == "bias_field_correction":
				image = bias_field_correction_image(image)

			elif self.name == "resize":
				width: int = int(next(iter(self.ranges[0])))
				height: int = int(next(iter(self.ranges[1])))
				if len(self.ranges) > 2:
					image = resize_image(image, width, height, Image.Resampling(next(iter(self.ranges[2]))))
				else:
					image = resize_image(image, width, height)

			elif self.name == "normalize":
				mini: float | int = next(iter(self.ranges[0]))
				maxi: float | int = next(iter(self.ranges[1]))
				norm_method: int = int(next(iter(self.ranges[2])))
				image = normalize_image(image, mini, maxi, norm_method)

			elif self.name == "median_blur":
				kernel_size: int = int(next(iter(self.ranges[0])))
				iterations: int = int(next(iter(self.ranges[1])))
				image = median_blur_image(image, kernel_size, iterations)

			elif self.name == "nlm_denoise":
				h: float = float(next(iter(self.ranges[0])))
				template_window_size: int = int(next(iter(self.ranges[1]))) if len(self.ranges) > 1 else 7
				search_window_size: int = int(next(iter(self.ranges[2]))) if len(self.ranges) > 2 else 21
				image = nlm_denoise_image(image, h, template_window_size, search_window_size)

			elif self.name == "bilateral_denoise":
				d: int = int(next(iter(self.ranges[0])))
				sigma_color: float = float(next(iter(self.ranges[1]))) if len(self.ranges) > 1 else 75.0
				sigma_space: float = float(next(iter(self.ranges[2]))) if len(self.ranges) > 2 else 75.0
				image = bilateral_denoise_image(image, d, sigma_color, sigma_space)

			elif self.name == "tv_denoise":
				weight: float = float(next(iter(self.ranges[0])))
				iterations: int = int(next(iter(self.ranges[1]))) if len(self.ranges) > 1 else 30
				method_value = str(next(iter(self.ranges[2]))) if len(self.ranges) > 2 else "chambolle"
				tv_method: Literal["chambolle", "bregman"] = "chambolle" if method_value == "chambolle" else "bregman"
				image = tv_denoise_image(image, weight, iterations, tv_method)

			elif self.name == "wavelet_denoise":
				wavelet_levels: int = int(next(iter(self.ranges[0])))
				wavelet_value = str(next(iter(self.ranges[1]))) if len(self.ranges) > 1 else "db1"
				mode_value = str(next(iter(self.ranges[2]))) if len(self.ranges) > 2 else "soft"
				# sigma is None by default in the function, so we don't provide it explicitly
				image = wavelet_denoise_image(
					image,
					wavelet=wavelet_value,
					mode=mode_value,
					wavelet_levels=wavelet_levels
				)

			elif self.name == "adaptive_denoise":
				method_value = str(next(iter(self.ranges[0])))
				if len(self.ranges) > 1:
					image = adaptive_denoise_image(image, method_value, float(next(iter(self.ranges[1]))))
				else:
					image = adaptive_denoise_image(image, method_value)

			elif self.name == "invert":
				image = invert_image(image)

			elif self.name == "custom":
				if self.custom is None:
					raise ValueError(
						"Custom processing technique is not defined, please set the custom attribute, "
						"ex: ProcessingTechnique('custom', custom=f)"
					)
				args: list[Any] = [next(iter(r)) for r in self.ranges]
				image = self.custom(image, *args)

			else:
				raise ValueError(f"Augmentation technique {self.name} is not supported.")

		return image

	def __call__(self, image: NDArray[Any], dividers: tuple[float, float] = (1.0, 1.0), times: int = 1) -> NDArray[Any]:
		""" Apply the processing technique to the image.

		Args:
			image		(NDArray[Any]):			Image to apply the processing technique to
			dividers	(tuple[float, float]):	Dividers used to adjust the processing technique parameters
				(default: (1.0, 1.0))
			times		(int):					Number of times to apply the processing technique
				(default: 1)
		Returns:
			NDArray[Any]: Processed image
		"""
		return self.apply(image, dividers, times)


# Recommendations enumerated
class RecommendedProcessingTechnique(Enum):
	""" A class containing the processing techniques with their recommended ranges based on scientific papers. """

	ROTATION = ProcessingTechnique("rotation", [RangeTuple(mini=-20, maxi=20, step=1, default=0)])
	""" Rotation between -20° and +20° is generally safe for medical images """

	TRANSLATION = ProcessingTechnique("translation", list(2 * [RangeTuple(mini=-0.15, maxi=0.15, step=0.01, default=0)]))
	""" Translation between -15% and 15% of image size """

	SHEARING = ProcessingTechnique("shearing", list(2 * [RangeTuple(mini=-10, maxi=10, step=1, default=0)]))
	""" Shearing between -10% and 10% distortion """

	AXIS_FLIP = ProcessingTechnique("axis_flip", [["horizontal"]], probability=0.5)
	""" Flipping: horizontal is much more used than vertical """

	NOISE = ProcessingTechnique("noise", [RangeTuple(mini=0.1, maxi=0.4, step=0.05, default=0.2)])
	""" Noise: FV values between 0.1 and 0.4 for gaussian noise """

	SALT_PEPPER = ProcessingTechnique("salt-pepper", [RangeTuple(mini=0.1, maxi=0.5, step=0.05, default=0.2)])
	""" Salt-pepper: densities between 0.1 and 0.5 """

	SHARPENING = ProcessingTechnique("sharpening", [RangeTuple(mini=0.5, maxi=1.5, step=0.1, default=1.1)])
	""" Sharpening: gaussian blur with variance=1 then subtract from original """

	CONTRAST = ProcessingTechnique("contrast", [RangeTuple(mini=0.7, maxi=1.3, step=0.1, default=1.1)])
	""" Contrast: linear scaling between min and max intensity """

	ZOOM = ProcessingTechnique("zoom", [RangeTuple(mini=0.85, maxi=1.15, step=0.05, default=1.05)])
	""" Zoom (Magnification): between 85% and 115% """

	BRIGHTNESS = ProcessingTechnique("brightness", [RangeTuple(mini=0.7, maxi=1.3, step=0.1, default=1.1)])
	""" Brightness: moderate changes to avoid losing details """

	BLUR = ProcessingTechnique("blur", [RangeTuple(mini=0.5, maxi=2, step=0.25, default=1)])
	""" Blur: gaussian blur preferred, moderate values """

	RANDOM_ERASE = ProcessingTechnique("random_erase", [RangeTuple(mini=0.01, maxi=0.1, step=0.01, default=0.05)])
	""" Random erasing: small regions to force model to learn descriptive features """

	CLAHE = ProcessingTechnique(
		"clahe",
		[
			RangeTuple(mini=1.0, maxi=4.0, step=0.5, default=2.0),  # clip_limit
			[8]  # tile_grid_size (fixed at 8x8)
		]
	)
	""" CLAHE: Contrast Limited Adaptive Histogram Equalization with recommended parameters """

	BINARY_THRESHOLD = ProcessingTechnique("binary_threshold", [RangeTuple(mini=0.1, maxi=0.9, step=0.1, default=0.5)])
	""" Binary threshold: threshold between 0.1 and 0.9 """

	THRESHOLD = ProcessingTechnique("threshold", [[0.3], [0.6]])
	""" Multi-level threshold: creates X levels of thresholding """

	CANNY = ProcessingTechnique("canny", [[50 / 255], [150 / 255], [3]])
	""" Canny edge detection with recommended parameters """

	LAPLACIAN = ProcessingTechnique("laplacian", [[3]])  # kernel_size
	""" Laplacian edge detection with 3x3 kernel """

	AUTO_CONTRAST = ProcessingTechnique("auto_contrast", [])
	""" Auto contrast the image """

	CURVATURE_FLOW_FILTER = ProcessingTechnique("curvature_flow_filter", [[0.05], [5]])
	""" Curvature flow filter with recommended parameters """

	BIAS_FIELD_CORRECTION = ProcessingTechnique("bias_field_correction", [])
	""" Bias field correction with recommended parameters """

	NORMALIZE = ProcessingTechnique("normalize", [[0], [255], [cv2.NORM_MINMAX]])
	""" Normalize the image to the range 0-255 """

	MEDIAN_BLUR = ProcessingTechnique("median_blur", [[7], [1]])
	""" Median blur with 7x7 kernel and 1 iteration """

	NLM_DENOISE = ProcessingTechnique("nlm_denoise", [
		RangeTuple(mini=5, maxi=20, step=1, default=10),  # h: affects the strength of the denoising
		[7],                                              # template_window_size: size of the template window
		[21]                                              # search_window_size: size of the search window
	])
	""" Non-local means denoising with recommended parameters """

	BILATERAL_DENOISE = ProcessingTechnique("bilateral_denoise", [
		[9],                                                 # diameter: size of the pixel neighborhood
		RangeTuple(mini=30, maxi=150, step=10, default=75),  # sigma_color: filter sigma in the color space
		RangeTuple(mini=30, maxi=150, step=10, default=75)   # sigma_space: filter sigma in the coordinate space
	])
	""" Bilateral filter denoising with recommended parameters """

	TV_DENOISE = ProcessingTechnique("tv_denoise", [
		RangeTuple(mini=0.05, maxi=0.5, step=0.05, default=0.1),   # weight: denoising weight
		[30],                                                      # max_iter: maximum number of iterations
		["chambolle"]                                              # method: algorithm used for denoising
	])
	""" Total variation denoising with recommended parameters """

	WAVELET_DENOISE = ProcessingTechnique("wavelet_denoise", [
		[3],        # wavelet_levels: number of wavelet decomposition levels
		["db1"],    # wavelet: wavelet to use
		["soft"]    # mode: thresholding mode
	])
	""" Wavelet denoising with recommended parameters """

	ADAPTIVE_DENOISE = ProcessingTechnique("adaptive_denoise", [
		["nlm"],                                               # method: denoising method to use
		RangeTuple(mini=0.1, maxi=0.9, step=0.1, default=0.5)  # strength: denoising strength parameter
	])
	""" Adaptive denoising with recommended parameters """

	INVERT = ProcessingTechnique("invert", [], probability=0.5)
	""" Invert the colors of an image with a 50% probability, hoping the model doesn't focus on bright parts only """

