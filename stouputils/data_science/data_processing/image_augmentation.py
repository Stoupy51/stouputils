
# Imports
import os
import random

from ...decorators import handle_error
from ..config.get import DataScienceConfig
from .image_preprocess import ImageDatasetPreprocess
from .technique import ProcessingTechnique


# Image dataset augmentation class
class ImageDatasetAugmentation(ImageDatasetPreprocess):
	""" Image dataset augmentation class. Check the class constructor for more information. """

	# Class constructor (configuration)
	def __init__(self, final_dataset_size: int, techniques: list[ProcessingTechnique] | None = None) -> None:
		""" Initialize the image dataset augmentation class with the given parameters.

		Args:
			final_dataset_size	(int):							Size of the final dataset
			techniques			(list[ProcessingTechnique]):	List of processing techniques to apply.
		"""
		if techniques is None:
			techniques = []
		super().__init__(techniques=techniques)
		self.final_dataset_size: int = final_dataset_size

	# Class methods
	def _add_suffix(self, path: str, used_destinations: set[str]) -> str:
		""" Add a count suffix to the path in order to avoid overwriting the same file

		Args:
			path	(str):	Path to the file (example: "path/to/file.jpg")
		Returns:
			str:	Path with the suffix (example: "path/to/file_1.jpg")
		"""
		# Split the path into base path and extension (e.g. "path/to/file.jpg" -> "path/to/file", ".jpg")
		path_no_ext, ext = os.path.splitext(path)

		# Convert count to augmented path
		def get_path_from_count(count: int) -> str:
			return path_no_ext + DataScienceConfig.AUGMENTED_FILE_SUFFIX + str(count) + ext

		# Function to check if the path is not available
		def is_not_available(path_aug: str) -> bool:
			return path_aug in used_destinations or os.path.isfile(path_aug)

		# Keep incrementing counter until we find a filename that doesn't exist
		count: int = 1
		while is_not_available(get_path_from_count(count)):
			count += 1
		return get_path_from_count(count)

	@handle_error(message="Error while getting queue of files to process")
	def get_queue(
		self,
		dataset_path: str,
		destination_path: str,
		images_per_class_dict: dict[str, int] | None = None
	) -> list[tuple[str, str, list[ProcessingTechnique]]]:
		""" Get the queue of images to process with their techniques.

		Args:
			dataset_path          (str):             Path to the dataset
			destination_path      (str):             Path to the destination dataset
			images_per_class_dict (dict[str, int]):  Dictionary mapping class names to desired number of images
				(optional, defaults to empty dictionary)
		Returns:
			list[tuple[str, str, list[ProcessingTechnique]]]: Queue of (source_path, dest_path, techniques) tuples
		"""
		# Initializations
		if images_per_class_dict is None:
			images_per_class_dict = {}
		queue: list[tuple[str, str, list[ProcessingTechnique]]] = []
		used_destinations: set[str] = set()

		# Get all folders (classes) and compute the number of images per class
		classes: tuple[str, ...] = tuple(f for f in os.listdir(dataset_path) if os.path.isdir(f"{dataset_path}/{f}"))
		default_images_per_class: int = self.final_dataset_size // len(classes)

		# For each class, for each image, apply the processing techniques
		for class_name in classes:
			class_path: str = f"{dataset_path}/{class_name}"
			images: list[str] = os.listdir(class_path)

			# Determine target number of images for this class
			target_images: int = images_per_class_dict.get(class_name, default_images_per_class)
			remaining_images: int = target_images - len(images)

			# Add images to the queue without applying the processing techniques
			for img in images:
				files: dict[str, str] = self.get_files_recursively(f"{class_path}/{img}", f"{destination_path}/{class_name}/{img}")
				for path, dest in files.items():
					queue.append((path, dest, []))

			# While there is less images than the desired number, apply the processing techniques
			while remaining_images > 0:
				chosen_images: list[str] = random.sample(images, k=min(remaining_images, len(images)))

				# Apply the processing techniques
				for img in chosen_images:
					img_destination: str = self._add_suffix(f"{destination_path}/{class_name}/{img}", used_destinations)
					used_destinations.add(img_destination)
					img_path: str = f"{class_path}/{img}"

					# Get the technique and their fixed values
					techniques: list[ProcessingTechnique] = [x.deterministic(use_default=False) for x in self.techniques]

					# For each image found, add it to the queue
					for path, dest in self.get_files_recursively(img_path, img_destination).items():
						queue.append((path, dest, techniques))

				# Update the remaining images
				remaining_images -= len(chosen_images)

		return queue

