
# Imports
import stouputils as stp

from stouputils.data_science.config.get import DataScienceConfig
from stouputils.data_science.data_processing.technique import ProcessingTechnique, RecommendedProcessingTechnique
from stouputils.data_science.scripts.augment_dataset import augment_dataset

# Constants
FINAL_DATASET_SIZE: int = 1000
TECHNIQUES: list[ProcessingTechnique] = [

	# Only keep bright enough parts 10% of the time hoping the models will concentrate on the prosthesis
	#ProcessingTechnique("custom", [[101], [0]], custom=keep_bright_enough_parts, probability=0.1),

	# Other techniques
	RecommendedProcessingTechnique.ROTATION.value / 2,
	# RecommendedProcessingTechnique.TRANSLATION.value,
	#RecommendedProcessingTechnique.SHEARING.value,
	RecommendedProcessingTechnique.AXIS_FLIP.value,
	# RecommendedProcessingTechnique.SALT_PEPPER.value,
	RecommendedProcessingTechnique.SHARPENING.value,
	RecommendedProcessingTechnique.CONTRAST.value,
	# RecommendedProcessingTechnique.ZOOM.value,
	RecommendedProcessingTechnique.BRIGHTNESS.value,
	# RecommendedProcessingTechnique.CLAHE.value,
	# RecommendedProcessingTechnique.BLUR.value,
	# RecommendedProcessingTechnique.RANDOM_ERASE.value,
	RecommendedProcessingTechnique.NOISE.value / 4,
	RecommendedProcessingTechnique.INVERT.value,
]

# Main function
def main() -> None:
	augment_dataset(TECHNIQUES, default_final_dataset_size=FINAL_DATASET_SIZE)


if __name__ == "__main__":
	stp.LogToFile.common(DataScienceConfig.LOGS_FOLDER, __file__, main)

