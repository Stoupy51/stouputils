
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportArgumentType=false
# pyright: reportCallIssue=false
# pyright: reportMissingTypeStubs=false

# Imports
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .image.canny import canny_image


def get_brightness_score(image: NDArray[Any], rect: Any, percentile: int = 95) -> float:
	""" Compute brightness score using high-percentile pixel intensity. """
	x, y, w, h = rect
	roi = image[y:y+h, x:x+w]

	# Use 95th percentile for brightness (high-density areas)
	high_intensity = np.percentile(roi, percentile)

	return float(high_intensity)

def get_contrast_score(image: NDArray[Any], rect: Any) -> float:
	""" Compute contrast score between object and surrounding background. """
	x, y, w, h = rect
	roi = image[y:y+h, x:x+w]

	# Define a slightly larger background region
	pad = max(w, h) // 10  # 10% padding
	x_bg, y_bg = max(0, x-pad), max(0, y-pad)
	w_bg, h_bg = min(image.shape[1] - x_bg, w + 2*pad), min(image.shape[0] - y_bg, h + 2*pad)

	background = image[y_bg:y_bg+h_bg, x_bg:x_bg+w_bg]

	# Compute contrast: Difference between ROI and background median
	contrast = np.median(roi) - np.median(background)

	return float(contrast)

def get_corners_distance(rect: Any, image_shape: tuple[int, int]) -> float:
	""" Compute average distance between rectangle corners and image center. """
	x, y, w, h = rect
	# Get the 4 corners of the rectangle
	corners = [
		(x, y),           # Top-left
		(x + w, y),       # Top-right
		(x, y + h),       # Bottom-left
		(x + w, y + h)    # Bottom-right
	]

	image_center_x = image_shape[1]/2
	image_center_y = image_shape[0]/2

	# Calculate distance from each corner to center
	distances = [
		np.sqrt((corner[0] - image_center_x)**2 + (corner[1] - image_center_y)**2)
		for corner in corners
	]

	# Return average distance
	return sum(distances) / len(distances)

def get_box_overlap_ratio(box1: Any, box2: Any) -> float:
	""" Compute overlap ratio between two bounding boxes with intersection area. """
	x1, y1, w1, h1 = box1
	x2, y2, w2, h2 = box2
	intersection_area = max(0, min(x1+w1, x2+w2) - max(x1, x2)) * max(0, min(y1+h1, y2+h2) - max(y1, y2))
	return intersection_area / min(w1 * h1, w2 * h2)

def get_fracture_score(image: NDArray[Any], rect: Any, padding: int = 20) -> float:
	""" Compute fracture score based on bone fractures around prosthesis. """
	x, y, w, h = rect

	# Add padding while ensuring we stay within image bounds
	x_pad = max(0, x - padding)
	y_pad = max(0, y - padding)
	w_pad = min(image.shape[1] - x_pad, w + 2*padding)
	h_pad = min(image.shape[0] - y_pad, h + 2*padding)

	# Extract padded ROI
	roi: NDArray[Any] = image[y_pad:y_pad+h_pad, x_pad:x_pad+w_pad]
	roi = cv2.normalize(roi, None, 0, 255, cv2.NORM_MINMAX)

	# Apply edge detection to find potential fracture lines
	edges = cv2.Canny(roi, 50, 150)

	# Count number of edge pixels
	edge_count = np.count_nonzero(edges)

	# Normalize by ROI area to get fracture score
	fracture_score = edge_count / (roi.shape[0] * roi.shape[1])
	return fracture_score


# Custom technique that segments the prosthesis from the image and zooms in on the prosthesis
def prosthesis_segmentation(image: NDArray[Any], debug_level: int = 0) -> NDArray[Any]:

	# Convert to RGB if needed
	image = np.array(Image.fromarray(image).convert("RGB"))

	# Convert to grayscale if needed
	gray: NDArray[Any] = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
	gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

	# Apply Canny edge detection
	mask: NDArray[Any] = gray.copy()
	mask = cv2.GaussianBlur(mask, (5,5), 0)
	mask = canny_image(mask, 50 / 255, 150 / 255)

	# Small gaps in the edges can break the contours. Try closing them.
	kernel: NDArray[Any] = np.ones((7,7), np.uint8)
	mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

	# Find contours
	contours: list[NDArray[Any]] = list(cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0])

	# Filter contours based on image size
	image_area: int = image.shape[0] * image.shape[1]
	min_area: int = int(0.05 * image_area)  # 5% of image
	max_area: int = int(0.60 * image_area)  # 60% of image

	# Filter contours based on area
	def get_area(rect: Any) -> int:
		return int(np.prod(rect[2:]))
	filtered_contours: list[NDArray[Any]] = [c for c in contours if min_area <= get_area(cv2.boundingRect(c)) <= max_area]

	# Apply median blur to the image (for better filtering)
	for _ in range(10):
		gray = cv2.medianBlur(gray, 15)

	## STRICT FILTERS
	# Only keep contours that has a height higher than the 60% of the width
	if True:
		def is_tall_enough(rect: Any) -> bool:
			return rect[3] > (rect[2] * 0.6)
		filtered_contours = [c for c in filtered_contours if is_tall_enough(cv2.boundingRect(c))]

	# Remove contours that are too thin (height > 4 * width)
	if True:
		def is_too_thin(rect: Any) -> bool:
			return rect[3] > rect[2] * 4
		filtered_contours = [c for c in filtered_contours if not is_too_thin(cv2.boundingRect(c))]

	# Only keep contours that are not touching two sides of the image
	# (excluding bottom unless it's more than 30% of the image width)
	if True:
		def is_touching_two_sides(box: Any) -> bool:
			x, y, w, h = box
			OFFSET: int = 5
			touches_left: bool = x < OFFSET
			touches_right: bool = x + w >= image.shape[1] - OFFSET
			touches_top: bool = y < OFFSET
			touches_bottom: bool = (y + h >= image.shape[0] - OFFSET) if (w > 0.3 * image.shape[1]) else False
			sides_touched: int = sum([touches_left, touches_right, touches_top, touches_bottom])
			return sides_touched >= 2

		filtered_contours = [c for c in filtered_contours if not is_touching_two_sides(cv2.boundingRect(c))]

	# Only keep contours that are not too dark (brightness score > 100)
	if True:
		def is_bright_enough(rect: Any) -> bool:
			return get_brightness_score(gray, rect) > 100
		filtered_contours = [c for c in filtered_contours if is_bright_enough(cv2.boundingRect(c))]

	## SOFT FILTERS (only apply if there are more than 1 contour)
	# Sort by brightness function
	def sort_by_brightness(c: Any) -> float:
		return get_brightness_score(gray, cv2.boundingRect(c))

	# Only keep contours that have more than 75% of the brightness that the best contour
	if True and len(filtered_contours) > 1:
		if filtered_contours:
			best_contour = sorted(filtered_contours, key=sort_by_brightness, reverse=True)[0]
			filtered_contours = [
				c for c in filtered_contours
				if sort_by_brightness(c) > sort_by_brightness(best_contour) * 0.75
			]

	# Remove contours that are too similar to each other
	if True and len(filtered_contours) > 1:
		def is_different(box1: Any, box2: Any) -> bool:
			return abs(box1[0] - box2[0]) > 10 or abs(box1[1] - box2[1]) > 10
		new_contours = []
		for c in filtered_contours:
			if all(is_different(cv2.boundingRect(c), cv2.boundingRect(other)) for other in new_contours):
				new_contours.append(c)
		filtered_contours = new_contours

	# If a contour's bounding box is at least 80% inside another contour's bounding box, remove the biggest one
	if True and len(filtered_contours) > 1:
		new_contours = []
		for c in sorted(filtered_contours, key=lambda c: get_area(cv2.boundingRect(c))):	# Sort by smallest area first
			if not any(
				get_box_overlap_ratio(cv2.boundingRect(c), cv2.boundingRect(other)) > 0.8
				for other in new_contours
			):
				new_contours.append(c)
		filtered_contours = new_contours

	# If a contour's bounding box is at least 30% inside another contour's bounding box,
	# keep the one with highest brightness score
	if True and len(filtered_contours) > 1:
		new_contours = []
		for c in sorted(filtered_contours, key=sort_by_brightness, reverse=True):	# Sort by highest brightness score
			if not any(
				get_box_overlap_ratio(cv2.boundingRect(c), cv2.boundingRect(other)) > 0.3
				for other in new_contours
			):
				new_contours.append(c)
		filtered_contours = new_contours

	# If the 5th percentile is too dark, remove it
	if True and len(filtered_contours) > 1:
		new_contours = []
		for c in filtered_contours:
			percentile: int = 5
			threshold: int = 100
			if np.percentile(gray, percentile) < threshold:
				new_contours.append(c)
		filtered_contours = new_contours

	# Only keep contours that have more than 85% of the brightness that the best contour
	if True and len(filtered_contours) > 1:
		if filtered_contours:
			best_contour = sorted(filtered_contours, key=sort_by_brightness, reverse=True)[0]
			filtered_contours = [
				c for c in filtered_contours
				if sort_by_brightness(c) > sort_by_brightness(best_contour) * 0.85
			]

	# Now sort by prosthesis score
	scores: dict[int, float] = {
		id(c): get_fracture_score(gray, cv2.boundingRect(c)) +
		get_brightness_score(gray, cv2.boundingRect(c)) / 255
		for c in filtered_contours
	}
	if True and len(filtered_contours) > 1:
		filtered_contours = sorted(
			filtered_contours,
			key=lambda c: scores[id(c)],
			reverse=True  # Highest score first
		)

	# Get the distance to the center of the image of the supposed prosthesis. Then, remove the contours
	# that are too far from the center (more than 50% of the image size) compared to the supposed prosthesis
	def get_distance_to_center(c: Any) -> float:
		x, y = cv2.boundingRect(c)[:2]
		return np.sqrt((x - image.shape[1]/2)**2 + (y - image.shape[0]/2)**2)
	if True and len(filtered_contours) > 1:
		distance = get_distance_to_center(filtered_contours[0])
		max_distance: float = max(image.shape[0], image.shape[1]) / 2
		filtered_contours = [c for c in filtered_contours if abs(get_distance_to_center(c) - distance) < max_distance]

	# If scores are too similar, and there are not centered (more than 5% of the image size), merge them
	if True and len(filtered_contours) > 1:
		max_distance: float = max(image.shape[0], image.shape[1]) / 20
		score_diff: float = abs(scores[id(filtered_contours[0])] - scores[id(filtered_contours[1])])
		contours_not_centered: bool = all(get_distance_to_center(c) > max_distance for c in filtered_contours[:2])
		if score_diff < 0.2 and contours_not_centered:
			filtered_contours = [
				cv2.convexHull(np.concatenate([filtered_contours[0], filtered_contours[1]])),
				*filtered_contours[2:]
			]

	# Normalize the image
	image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)

	# Debug mode (show the mask)
	if debug_level > 0:
		if debug_level > 2:
			image = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

		# Add bounding boxes to visualize detected regions
		for i, contour in enumerate(filtered_contours):
			x, y, w, h = cv2.boundingRect(contour)
			color = (0, 255, 0) if i == 0 else (255, 0, 0)  # Green for best match, blue for second
			cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

	else:
		# Get the best contour's bounding rectangle and crop to it
		if len(filtered_contours) > 0:
			# Get bounding box of best contour
			x, y, w, h = cv2.boundingRect(filtered_contours[0])

			# Add padding
			padding: int = 10
			x = max(0, x - padding)
			y = max(0, y - padding)
			w = min(image.shape[1] - x, w + 2*padding)
			h = min(image.shape[0] - y, h + 2*padding)

			# Crop image to bounding box
			output: NDArray[Any] = image[y:y+h, x:x+w]
			return output

	# No prosthesis found, keep the original image
	return image


# Custom technique that only keeps the brightest parts of the image
def keep_bright_enough_parts(
	image: NDArray[Any],
	window_size: int = 101,
	invert: bool = False,
	debug_level: int = 0
	) -> NDArray[Any]:
	""" Keep only the brightest parts of the image.

	For each pixel, if the window around it is brighter than 60% of the brightest pixels in the image, keep it.

	Args:
		image                (NDArray[Any]):    Image to process.
		window_size          (int):           Size of the window to consider around each pixel.
		invert               (bool):          Instead of keeping the brightest parts, keep the darkest parts.
		debug_level          (int):           Debug level.

	Returns:
		NDArray[Any]: Processed image with only bright parts preserved.
	"""
	new_image: NDArray[Any] = image.copy()

	# Create a mask for bright regions
	mask: NDArray[Any] = np.zeros_like(image, dtype=bool)
	image_brightness: float = float(np.percentile(image, 60 if not invert else 40))

	# Blur the image
	image = cv2.GaussianBlur(image, (window_size, window_size), 0)

	# Use vectorized operations instead of pixel-by-pixel loop
	# Calculate brightness scores for all pixels at once
	from scipy.ndimage import maximum_filter, minimum_filter

	# Calculate average brightness in window around each pixel
	if invert:
		avg_brightness: NDArray[Any] = minimum_filter(image.astype(float), size=window_size)
	else:
		avg_brightness: NDArray[Any] = maximum_filter(image.astype(float), size=window_size)

	# Create mask where brightness exceeds threshold
	if invert:
		mask = avg_brightness < image_brightness
	else:
		mask = avg_brightness > image_brightness

	# Apply mask to create output image
	new_image[~mask] = 0

	if debug_level > 0:
		return image
	else:
		return new_image

