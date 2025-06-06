
# Imports
import stouputils as stp

from stouputils.data_science.config.get import DataScienceConfig
from stouputils.data_science.scripts.routine import routine


# Main function
def main() -> None:

	# Specify additional training data paths
	additional_training_paths: list[str] = [f"{DataScienceConfig.DATA_FOLDER}/more_pizza"]

	# Launch the script
	routine(add_to_train_only=additional_training_paths)


if __name__ == "__main__":
	stp.LogToFile.common(DataScienceConfig.LOGS_FOLDER, __file__, main)

