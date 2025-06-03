
# Imports
import argparse
import os
import sys

from ...decorators import handle_error, measure_time
from ...print import info
from ...parallel import multithreading
from ..config.get import DataScienceConfig
from ..dataset import LOWER_GS
from ..models.all import ALL_MODELS, CLASS_MAP

# Constants
MODEL_HELP: str = "Model to use"
KFOLD_HELP: str = "Number of folds for k-fold cross validation (0 = no k-fold)"
TRANSFER_LEARNING_HELP: str = "Transfer learning source (imagenet, None, \"data/dataset_name\")"
GROUPING_HELP: str = "Grouping strategy for the dataset"
GROUPING_CHOICES: tuple[str, ...] = (*LOWER_GS, "all")
GRID_SEARCH_HELP: str = "If grid search should be performed on hyperparameters"
MAX_WORKERS_HELP: str = "Maximum number of threads for processing"
VERBOSE_HELP: str = "Verbosity level"
PARSER_DESCRIPTION: str = "Command-line interface for exhaustive process."


# Main function
@measure_time(info, "Total execution time of the script")
@handle_error(exceptions=(KeyboardInterrupt, Exception), error_log=DataScienceConfig.ERROR_LOG)
def exhaustive_process(
	datasets_to_process: list[tuple[str, str]],
	main_script_path: str,

	default_kfold: int = 0,
	default_transfer_learning: str = "imagenet",
	default_grouping: str = "none",
	default_max_workers: int = 1,
	default_verbose: int = 100,
) -> None:
	""" Process all datasets through preprocessing, augmentation, and training.

	This script will:
	1. Verify if the datasets exist
	2. Prepare commands for training models on each dataset
	3. Execute the commands with the specified parameters
	4. Support multiple grouping strategies and model architectures
	5. Allow for k-fold cross-validation and grid search optimization

	Args:
		datasets_to_process (list[tuple[str, str]]): List of dataset paths to process.
			Each tuple contains (dataset_path, based_of_path), e.g. [("aug_preprocessed_path", "preprocessed_path")].
		main_script_path (str): Path to the main script, e.g. "src/main.py"
		default_model (str): Default model architecture to use for training.
		default_kfold (int): Default number of folds for k-fold cross validation.
		default_transfer_learning (str): Default source for transfer learning.
		default_grouping_strategy (str): Default strategy for grouping dataset images.
		default_max_workers (int): Default maximum number of threads for processing.
		default_verbose (int): Default verbosity level for training output.

	Returns:
		None: This function does not return anything.
	"""
	info("Starting the script...")

	# Parse the arguments
	parser = argparse.ArgumentParser(description=PARSER_DESCRIPTION)
	parser.add_argument("--model", type=str, choices=ALL_MODELS, help=MODEL_HELP)
	parser.add_argument("--kfold", type=int, default=default_kfold, help=KFOLD_HELP)
	parser.add_argument("--transfer_learning", type=str, default=default_transfer_learning, help=TRANSFER_LEARNING_HELP)
	parser.add_argument("--grouping_strategy", type=str, default=default_grouping, choices=GROUPING_CHOICES, help=GROUPING_HELP)
	parser.add_argument("--grid_search", action="store_true", help=GRID_SEARCH_HELP)
	parser.add_argument("--max_workers", type=int, default=default_max_workers, help=MAX_WORKERS_HELP)
	parser.add_argument("--verbose", type=int, default=default_verbose, help=VERBOSE_HELP)
	args: argparse.Namespace = parser.parse_args()

	# Extract more arguments
	grouping_strategies: tuple[str, ...] = LOWER_GS if args.grouping_strategy == "all" else (args.grouping_strategy,)

	# Step 1: Verify if the datasets exist
	for dataset_path, based_of in datasets_to_process:
		if not os.path.exists(dataset_path):
			raise FileNotFoundError(f"Dataset not found: '{dataset_path}'")
		if based_of and not os.path.exists(based_of):
			raise FileNotFoundError(f"Based of dataset not found: '{based_of}'")


	# Step 2: Prepare all commands
	commands: list[str] = []
	for dataset_path, based_of in datasets_to_process:
		for grouping_strategy in grouping_strategies:
			info(f"Training on dataset: {dataset_path}")
			based_of_arg: str = f"--based_of {based_of} " if based_of else ""
			grid_search_arg: str = "--grid_search " if args.grid_search else ""

			# Iterate over each model in ROUTINE_MAP
			for model_names in CLASS_MAP.values():

				# Check if the model is in the list of model names
				if args.model in model_names:

					# Get the model name from the list of model names
					# Ex: "good" is in ("densenet121", "densenets", "all", "good"), we take the first one: "densenet121"
					model_name: str = model_names[0]

					# Build base command
					base_cmd: str = (
						f"{sys.executable} {main_script_path} "
						f"--model {model_name} "
						f"--verbose {args.verbose} "
						f"--input {dataset_path} "
						f"--transfer_learning {args.transfer_learning} "
						f"--grouping_strategy {grouping_strategy} "
						f"{based_of_arg}"
						f"{grid_search_arg}"
					)

					# Single run with or without k-fold based on args.kfold
					kfold_arg: str = f"--kfold {args.kfold}" if args.kfold != 0 else ""
					commands.append(f"{base_cmd} {kfold_arg}")

	# Run all commands
	def runner(cmd: str) -> None:
		info(f"Executing command: '{cmd}'")
		sys.stdout.flush()
		sys.stderr.flush()
		os.system(cmd)
	multithreading(
		runner,
		commands,
		desc="Processing all datasets",
		max_workers=args.max_workers,
		delay_first_calls=2.0
	)

