""" Package for advanced dataset handling.

Provides comprehensive tools for loading, processing and managing image datasets
with special handling for augmented data and group-aware operations.

Main Components:

- Dataset            : Core class for storing and managing dataset splits with metadata
- DatasetLoader      : Handles dataset loading from directories with various strategies
- DatasetSplitter    : Manages stratified splitting while maintaining group integrity
- GroupingStrategy   : Enum defining image grouping approaches (NONE/SIMPLE/CONCATENATE)
- XyTuple            : Specialized container for features/labels with file tracking

Key Features:

- Augmented data handling with original file mapping
- Prevention of data leakage between train/test sets
- Support for multiple grouping strategies at subject/image level
- Class-aware dataset splitting with stratification
- Comprehensive metadata tracking (class distributions, file paths)
- Compatibility with keras.image_dataset_from_directory
- Group-aware k-fold cross validation support
"""

# Imports
from .dataset import Dataset
from .dataset_loader import DatasetLoader
from .grouping_strategy import GroupingStrategy
from .image_loader import ALLOWLIST_FORMATS, load_images_from_directory
from .xy_tuple import XyTuple

# Constants
LOWER_GS: tuple[str, ...] = tuple(x.name.lower() for x in GroupingStrategy)

# Exports
__all__ = [
    "ALLOWLIST_FORMATS",
    "LOWER_GS",
    "Dataset",
    "DatasetLoader",
    "GroupingStrategy",
    "XyTuple",
    "load_images_from_directory",
]

