
# Imports
import argparse
import itertools
from typing import Any, Literal

from ...decorators import handle_error, measure_time
from ...print import info, error, progress
from ...io import clean_path
from ..config.get import DataScienceConfig
from ..dataset import LOWER_GS, Dataset, DatasetLoader, GroupingStrategy, XyTuple
from ..models.all import ALL_MODELS, CLASS_MAP, ModelInterface

# Constants
MODEL_HELP: str             = "Model(s) name or alias to use"
INPUT_HELP: str             = "Path to the dataset, e.g. 'data/aug_hip_implant'"
BASED_OF_HELP: str          = "Path to the base dataset for filtering train/test, e.g. 'data/hip_implant'"
TRANSFER_LEARNING_HELP: str = "Transfer learning source (imagenet, None, 'data/dataset_folder')"
GROUPING_HELP: str          = "Grouping strategy for the dataset"
K_FOLD_HELP: str            = "Number of folds for k-fold cross validation (0 = no k-fold, negative = LeavePOut)"
GRID_SEARCH_HELP: str       = "If grid search should be performed on hyperparameters"
VERBOSE_HELP: str           = "Verbosity level sent to functions"
PARSER_DESCRIPTION: str     = "Command-line interface for training and evaluating machine learning models."


# Main function
@measure_time(info, "Total execution time of the script")
@handle_error(exceptions=(KeyboardInterrupt, Exception), error_log=DataScienceConfig.ERROR_LOG)
def routine(
	default_input: str = f"{DataScienceConfig.DATA_FOLDER}/aug_hip_implant_preprocessed",
	default_based_of: str = "auto",
	default_transfer_learning: str = "imagenet",
	default_grouping_strategy: str = "none",
	default_kfold: int = 0,
	default_verbose: int = 100,

	loading_type: Literal["image"] = "image",
	grid_search_param_grid: dict[str, list[Any]] | None = None,
	add_to_train_only: list[str] | None = None,
) -> None:
	""" Main function of the script for training and evaluating machine learning models.

	This function handles the entire workflow for model training and evaluation, including:
	- Parsing command-line arguments (default values are set in the function signature)
	- Loading and preparing datasets with configurable grouping strategies
	- Supporting transfer learning from various sources
	- Enabling K-fold cross-validation, LeavePOut or LeaveOneOut
	- Providing grid search capabilities for hyperparameter optimization
	- Incorporating additional training data from specified paths

	Args:
		default_input             (str):              Default path to the dataset to use.
		default_based_of          (str):              Default path to the base dataset for filtering train/test data.
		default_transfer_learning (str):              Default transfer learning source.
		default_grouping_strategy (str):              Default grouping strategy for the dataset.
		default_kfold             (int):              Default number of folds for k-fold cross validation.
		default_verbose           (int):              Default verbosity level.
		loading_type              (Literal["image"]):             Type of data to load, currently only supports "image".
		grid_search_param_grid    (dict[str, list[Any]] | None):  Parameters grid for hyperparameter optimization.
		add_to_train_only         (list[str] | None):             List of paths to additional training datasets.

	Returns:
		None: This function does not return anything.
	"""
	if grid_search_param_grid is None:
		grid_search_param_grid = {"batch_size": [8, 16, 32, 64]}
	if add_to_train_only is None:
		add_to_train_only = []

	info("Starting the script...")

	# Parse the arguments
	parser = argparse.ArgumentParser(description=PARSER_DESCRIPTION)
	parser.add_argument("--model",             type=str, choices=ALL_MODELS, required=True, help=MODEL_HELP)
	parser.add_argument("--input",             type=str, default=default_input, help=INPUT_HELP)
	parser.add_argument("--based_of",          type=str, default=default_based_of, help=BASED_OF_HELP)
	parser.add_argument("--transfer_learning", type=str, default=default_transfer_learning, help=TRANSFER_LEARNING_HELP)
	parser.add_argument("--grouping_strategy", type=str, default=default_grouping_strategy, choices=LOWER_GS, help=GROUPING_HELP)
	parser.add_argument("--kfold", type=int, default=default_kfold, help=K_FOLD_HELP)
	parser.add_argument("--grid_search", action="store_true", help=GRID_SEARCH_HELP)
	parser.add_argument("--verbose", type=int, default=default_verbose, help=VERBOSE_HELP)
	args: argparse.Namespace = parser.parse_args()
	model: str = args.model.lower()
	kfold: int = args.kfold
	input_path: str = clean_path(args.input, trailing_slash=False)
	based_of: str = clean_path(args.based_of, trailing_slash=False)
	transfer_learning: str = clean_path(args.transfer_learning, trailing_slash=False)
	verbose: int = args.verbose
	grouping_strategy: str = args.grouping_strategy
	grid_search: bool = args.grid_search

	# If based_of is "auto", set it to the input path without the "aug"
	if based_of == "auto":
		prefix: str = "/" + DataScienceConfig.AUGMENTED_DIRECTORY_PREFIX
		if prefix in input_path:
			based_of = input_path.replace(prefix, "/")
		else:
			based_of = ""

	# Load the dataset
	kwargs: dict[str, Any] = {}
	if grouping_strategy == "concatenate":
		kwargs["color_mode"] = "grayscale"
	dataset: Dataset = DatasetLoader.from_path(
		path=input_path,
		loading_type=loading_type,
		seed=DataScienceConfig.SEED,
		test_size=DataScienceConfig.TEST_SIZE,
		grouping_strategy=next(x for x in GroupingStrategy if x.name.lower() == grouping_strategy),
		based_of=based_of,
		**kwargs
	)
	info(dataset)

	# Define parameter combinations
	param_combinations: list[dict[str, Any]] = [{}]  # Default empty params
	if grid_search:

		# Generate all parameter combinations
		param_combinations.clear()
		for values in itertools.product(*grid_search_param_grid.values()):
			param_combinations.append(dict(zip(grid_search_param_grid.keys(), values, strict=False)))

	# Load additional training data from provided paths
	additional_training_data: XyTuple = XyTuple.empty()
	for path in add_to_train_only:
		try:
			additional_dataset: Dataset = DatasetLoader.from_path(
				path=path,
				loading_type=loading_type,
				seed=DataScienceConfig.SEED,
				test_size=0,  # Use all data for training
				**kwargs
			)
			additional_training_data += additional_dataset.training_data
		except Exception as e:
			error(f"Failed to load additional training data from '{path}': {e}")

	# Prepare the initialization arguments
	# (num_classes: int, kfold: int = 0, transfer_learning: str = "imagenet", **override_params: Any)
	initialization_args: dict[str, Any] = {

		# Mandatory arguments
		"num_classes": dataset.num_classes,
		"kfold": kfold,
		"transfer_learning": transfer_learning,

		# Optional arguments (override_params)
		"additional_training_data": additional_training_data
	}

	# Collect all class routines that match the model name
	classes: list[type[ModelInterface]] = [key for key, values in CLASS_MAP.items() if model in values]

	# For each parameter combination
	for i, params in enumerate(param_combinations):
		if grid_search:
			progress(f"Grid search {i+1}/{len(param_combinations)}, Training with parameters:\n{params}")
			initialization_args["override_params"] = params

		# Launch all class routines
		for class_to_process in classes:
			model_instance: ModelInterface = class_to_process(**initialization_args)
			trained_model: ModelInterface = model_instance.routine_full(dataset, verbose)
			info(trained_model)
			del trained_model
	return

