
# Imports
import os
import shutil
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray

from ...decorators import handle_error
from ...parallel import multiprocessing, CPU_COUNT
from ...print import warning, error
from ...io import clean_path, super_copy
from .technique import ProcessingTechnique


# Image dataset augmentation class
class ImageDatasetPreprocess:
	""" Image dataset preprocessing class. Check the class constructor for more information. """

	# Class constructor (configuration)
	def __init__(self, techniques: list[ProcessingTechnique] | None = None) -> None:
		""" Initialize the image dataset augmentation class with the given parameters.

		Args:
			techniques			(list[ProcessingTechnique]):	List of processing techniques to apply.
		"""
		if techniques is None:
			techniques = []
		assert all(isinstance(x, ProcessingTechnique) for x in techniques), (
			"All techniques must be ProcessingTechnique objects"
		)
		self.techniques: list[ProcessingTechnique] = [x.deterministic(use_default=True) for x in techniques]

	@handle_error(message="Error while getting files recursively")
	def get_files_recursively(
		self,
		source: str,
		destination: str,
		extensions: tuple[str,...] = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif")
	) -> dict[str, str]:
		""" Recursively get all files in a directory and their destinations.

		Args:
			source		(str):				Path to the source directory
			destination	(str):				Path to the destination directory
			extensions	(tuple[str,...]):	Tuple of extensions to consider (e.g. (".jpg", ".png"))
		Returns:
			dict[str, str]:	Dictionary mapping source paths to destination paths
		"""
		files: dict[str, str] = {}

		if os.path.isfile(source) and source.endswith(extensions):
			files[source] = destination
		elif os.path.isdir(source):
			for item in os.listdir(source):
				item_path: str = f"{source}/{item}"
				item_dest: str = f"{destination}/{item}"
				files.update(self.get_files_recursively(item_path, item_dest, extensions))
		return files


	@handle_error(message="Error while getting queue of files to process")
	def get_queue(self, dataset_path: str, destination_path: str) -> list[tuple[str, str, list[ProcessingTechnique]]]:
		""" Get the queue of images to process with their techniques.

		This method converts the processing techniques ranges to fixed values and builds a queue
		of files to process by recursively finding all images in the dataset path.

		Args:
			dataset_path		(str):		Path to the dataset directory
			destination_path	(str):		Path to the destination directory where processed images will be saved
		Returns:
			list[tuple[str, str, list[ProcessingTechnique]]]: Queue of (source_path, dest_path, techniques) tuples
		"""
		# Convert technique ranges to fixed values
		self.techniques = [x.deterministic(use_default=True) for x in self.techniques]

		# Build queue by recursively finding all images and their destinations
		return [
			(path, dest, self.techniques)
			for path, dest in
			self.get_files_recursively(dataset_path, destination_path).items()
		]


	@handle_error(message="Error while processing the dataset")
	def process_dataset(
		self,
		dataset_path: str,
		destination_path: str,
		max_workers: int = CPU_COUNT,
		ignore_confirmation: bool = False
	) -> None:
		""" Preprocess the dataset by applying the given processing techniques to the images.

		Args:
			dataset_path		(str):		Path to the dataset
			destination_path	(str):		Path to the destination dataset
			max_workers			(int):		Number of workers to use (Defaults to CPU_COUNT)
			ignore_confirmation	(bool):		If True, don't ask for confirmation
		"""
		# Clean paths
		dataset_path = clean_path(dataset_path)
		destination_path = clean_path(destination_path)

		# If destination folder exists, ask user if they want to delete it
		if os.path.isdir(destination_path):
			if not ignore_confirmation:
				warning(f"Destination folder '{destination_path}' already exists.\nDo you want to delete it? (y/N)")
				if input().lower() == "y":
					shutil.rmtree(destination_path)
				else:
					error("Aborting...", exit=False)
					return
			else:
				warning(f"Destination folder '{destination_path}' already exists.\nDeleting it...")
				shutil.rmtree(destination_path)

		# Prepare the multiprocessing arguments (image path, destination path, techniques)
		queue: list[tuple[str, str, list[ProcessingTechnique]]] = self.get_queue(dataset_path, destination_path)

		# Apply the processing techniques in parallel
		splitted: list[str] = dataset_path.split('/')
		short_path: str = f".../{splitted[-1]}" if len(splitted) > 2 else dataset_path
		multiprocessing(
			self.apply_techniques,
			queue,
			use_starmap=True,
			desc=f"Processing dataset '{short_path}'",
			max_workers=max_workers
		)


	@staticmethod
	def apply_techniques(path: str, dest: str, techniques: list[ProcessingTechnique], use_padding: bool = True) -> None:
		""" Apply the processing techniques to the image.

		Args:
			path		(str):							Path to the image
			dest		(str):							Path to the destination image
			techniques	(list[ProcessingTechnique]):	List of processing techniques to apply
			use_padding	(bool):							If True, add padding to the image before applying techniques
		"""
		if not techniques:
			super_copy(path, dest)
			return

		# Read the image
		img: NDArray[Any] = cv2.imread(path, cv2.IMREAD_UNCHANGED)

		if not use_padding:
			# Add a padding (to avoid cutting the image)
			previous_shape: tuple[int, ...] = img.shape[:2]
			padding: int = max(previous_shape[0], previous_shape[1]) // 2
			img = np.pad( # pyright: ignore [reportUnknownMemberType]
				img,
				pad_width=((padding, padding), (padding, padding), (0, 0)),
				mode="constant",
				constant_values=0
			)

			# Compute the dividers that will be used to adjust techniques parameters
			dividers: tuple[float, float] = (
				img.shape[0] / previous_shape[0],
				img.shape[1] / previous_shape[1]
			)
		else:
			dividers = (1.0, 1.0)
			padding = 0

		# Apply the processing techniques
		for technique in techniques:
			img = technique.apply(img, dividers)

		# Remove the padding
		if not use_padding:
			img = img[padding:-padding, padding:-padding, :]

		# Save the image
		os.makedirs(os.path.dirname(dest), exist_ok=True)
		cv2.imwrite(dest, img)
