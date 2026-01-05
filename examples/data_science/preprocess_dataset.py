
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
import stouputils as stp

from stouputils.data_science.config.get import DataScienceConfig
from stouputils.data_science.data_processing.prosthesis_detection import prosthesis_segmentation
from stouputils.data_science.data_processing.technique import ProcessingTechnique, RecommendedProcessingTechnique
from stouputils.data_science.scripts.preprocess_dataset import preprocess_dataset

# Constants
TECHNIQUES: list[ProcessingTechnique] = [
	# Segmentation
	#ProcessingTechnique("custom", [[0]], custom=prosthesis_segmentation),

	# Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
	RecommendedProcessingTechnique.CLAHE.value.deterministic(use_default=True),

	# Sharpening
	RecommendedProcessingTechnique.SHARPENING.value.deterministic(use_default=True),

	# Normalize
	RecommendedProcessingTechnique.NORMALIZE.value,
]

# Main function
def main() -> None:
	preprocess_dataset(TECHNIQUES)


if __name__ == "__main__":
	stp.LogToFile.common(DataScienceConfig.LOGS_FOLDER, __file__, main)

