
# Imports
import stouputils as stp

from stouputils.data_science.config.get import DataScienceConfig
from stouputils.data_science.scripts.exhaustive_process import exhaustive_process


# Main function
def main() -> None:

	# Define dataset paths
	preprocessed_path: str = f"{DataScienceConfig.DATA_FOLDER}/hip_implant_preprocessed"
	aug_preprocessed_path: str = f"{DataScienceConfig.DATA_FOLDER}/aug_hip_implant_preprocessed"

	# Prepare the datasets to process
	datasets: list[tuple[str, str]] = [
		(aug_preprocessed_path, preprocessed_path),  # Augmented preprocessed dataset
	]

	# Launch the exhaustive process
	exhaustive_process(
		datasets_to_process=datasets,
		main_script_path=f"{DataScienceConfig.ROOT}/src/routine.py",
	)


if __name__ == "__main__":
	stp.LogToFile.common(DataScienceConfig.LOGS_FOLDER, __file__, main)

