
# Imports
import argparse
from typing import Literal

from ...decorators import handle_error, measure_time
from ...print import info
from ...io import clean_path
from ..config.get import DataScienceConfig
from ..data_processing.image_augmentation import ImageDatasetAugmentation
from ..data_processing.technique import ProcessingTechnique

# Constants
CONFIRMATION_HELP: str = "Don't ask for confirmation"
TYPE_HELP: str = "Type of data to augment"
INPUT_HELP: str = "Path to input dataset"
OUTPUT_HELP: str = "Path to save augmented dataset (Defaults to input path prefixed with 'aug_')"
PARSER_DESCRIPTION: str = "Command-line interface for augmenting a dataset with various techniques."
FINAL_DATASET_SIZE_HELP: str = "Final size of the dataset"


# Main function
@measure_time(info, "Total execution time of the script")
@handle_error(exceptions=(KeyboardInterrupt, Exception), error_log=DataScienceConfig.ERROR_LOG)
def augment_dataset(
	techniques: list[ProcessingTechnique],

    default_type: Literal["image"] = "image",
    default_input: str = f"{DataScienceConfig.DATA_FOLDER}/hip_implant",
    default_output: str = "",
    default_final_dataset_size: int = 1000,
) -> None:
	""" Augment a dataset with various data processing techniques.

	This script takes a dataset path and applies configurable processing techniques
	to generate an expanded dataset. The augmented data is saved to a destination path.
	The augmentation can be done for images or other data types.

	Args:
		default_type   (str): Default type of data to augment.
		default_input  (str): Default path to the input dataset.
		default_output (str): Default path to save the augmented dataset.
		default_final_dataset_size (int): Default final size of the dataset.

	Returns:
		None: This function does not return anything.
	"""
	info("Starting the script...")

	# Parse the arguments
	parser = argparse.ArgumentParser(description=PARSER_DESCRIPTION)
	parser.add_argument("-y", action="store_true", help=CONFIRMATION_HELP)
	parser.add_argument("--type",   type=str, default=default_type, choices=["image"], help=TYPE_HELP)
	parser.add_argument("--input",  type=str, default=default_input, help=INPUT_HELP)
	parser.add_argument("--output", type=str, default=default_output, help=OUTPUT_HELP)
	parser.add_argument("--final_dataset_size", type=int, default=default_final_dataset_size, help=FINAL_DATASET_SIZE_HELP)
	args: argparse.Namespace = parser.parse_args()
	data_type: str = args.type
	input_path: str = clean_path(args.input, trailing_slash=False)
	output_path: str = clean_path(args.output, trailing_slash=False)
	final_dataset_size: int = args.final_dataset_size
	info(f"Augmenting dataset from '{input_path}' to '{output_path}' with {final_dataset_size} samples")

	# Check if the output path is provided, if not,
	# use the input path prefixed with "aug_" (ex: .../data/hip_implant -> .../data/aug_hip_implant)
	if not output_path:
		splitted: list[str] = input_path.split("/")
		splitted[-1] = DataScienceConfig.AUGMENTED_DIRECTORY_PREFIX + splitted[-1]
		output_path = "/".join(splitted)
		info(f"Output path not provided, using variant of input path: '{output_path}'")

	# Augment the dataset
	if data_type == "image":
		augmentation = ImageDatasetAugmentation(final_dataset_size, techniques)
		augmentation.process_dataset(input_path, output_path, ignore_confirmation=args.y)
	return

