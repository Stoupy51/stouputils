
# Imports
import argparse
from typing import Literal

from ...decorators import handle_error, measure_time
from ...print import info
from ...io import clean_path
from ..config.get import DataScienceConfig
from ..data_processing.image_preprocess import ImageDatasetPreprocess
from ..data_processing.technique import ProcessingTechnique

# Constants
CONFIRMATION_HELP: str = "Don't ask for confirmation"
TYPE_HELP: str = "Type of data to preprocess"
INPUT_HELP: str = "Path to input dataset"
OUTPUT_HELP: str = "Path to save preprocessed dataset"
PARSER_DESCRIPTION: str = "Command-line interface for preprocessing a dataset with various techniques."


# Main function
@measure_time(info, "Total execution time of the script")
@handle_error(exceptions=(KeyboardInterrupt, Exception), error_log=DataScienceConfig.ERROR_LOG)
def preprocess_dataset(
	techniques: list[ProcessingTechnique],

	default_type: Literal["image"] = "image",
	default_input: str = f"{DataScienceConfig.DATA_FOLDER}/hip_implant",
	default_output: str = "",
) -> None:
	""" Preprocess a dataset by applying image processing techniques.

	This function takes a dataset path and applies various techniques
	to create new dataset at the specified destination path.

	Args:
		techniques (list[ProcessingTechnique]): List of techniques to apply to the dataset.
		default_type (str): Default type of data to preprocess.
		default_input (str): Default path to the input dataset.
		default_output (str): Default path to save the preprocessed dataset.

	Returns:
		None: The function modifies files on disk but does not return anything.
	"""
	info("Starting the script...")

	# Parse the arguments
	parser = argparse.ArgumentParser(description=PARSER_DESCRIPTION)
	parser.add_argument("-y", action="store_true", help=CONFIRMATION_HELP)
	parser.add_argument("--type", type=str, default=default_type, choices=["image"], help=TYPE_HELP)
	parser.add_argument("--input", type=str, default=default_input, help=INPUT_HELP)
	parser.add_argument("--output", type=str, default=default_output, help=OUTPUT_HELP)
	args: argparse.Namespace = parser.parse_args()
	data_type: str = args.type
	input_path: str = clean_path(args.input, trailing_slash=False)
	output_path: str = clean_path(args.output, trailing_slash=False)

	# Check if the output path is provided, if not,
	# use the input path suffixed with "_preprocessed"
	if not output_path:
		splitted: list[str] = input_path.split("/")
		splitted[-1] = splitted[-1] + DataScienceConfig.PREPROCESSED_DIRECTORY_SUFFIX
		output_path = "/".join(splitted)
		info(f"Output path not provided, using variant of input path: '{output_path}'")

	# Preprocess the dataset
	if data_type == "image":
		preprocess: ImageDatasetPreprocess = ImageDatasetPreprocess(techniques)
		preprocess.process_dataset(input_path, output_path, ignore_confirmation=args.y)

