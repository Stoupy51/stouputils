"""
This module contains the MetricUtils class, which provides static methods for
calculating various metrics for machine learning tasks.

This class contains static methods for:

- Calculating various metrics (accuracy, precision, recall, etc.)
- Computing confusion matrix and related metrics
- Generating ROC curves and finding optimal thresholds
- Calculating F-beta scores

The metrics are calculated based on the predictions made by a model and the true labels from a dataset.
The class supports both binary and multiclass classification tasks.
"""
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportMissingTypeStubs=false

# Imports
import os
from collections.abc import Iterable
from typing import Any, Literal

import mlflow
import numpy as np
from ..decorators import handle_error, measure_time
from ..print import info, warning
from matplotlib import pyplot as plt
from numpy.typing import NDArray
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix, matthews_corrcoef

from .config.get import DataScienceConfig
from .dataset import Dataset
from .metric_dictionnary import MetricDictionnary
from .utils import Utils


# Class
class MetricUtils:
	""" Class containing static methods for calculating metrics. """

	@staticmethod
	@measure_time(info, "Execution time of MetricUtils.metrics")
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def metrics(
		dataset: Dataset,
		predictions: Iterable[Any],
		run_name: str,
		mode: Literal["binary", "multiclass", "none"] = "binary"
	) -> dict[str, float]:
		""" Method to calculate as many metrics as possible for the given dataset and predictions.

		Args:
			dataset		(Dataset):		Dataset containing the true labels
			predictions	(Iterable):		Predictions made by the model
			run_name	(str):			Name of the run, used to save the ROC curve
			mode		(Literal):		Mode of the classification, defaults to "binary"
		Returns:
			dict[str, float]:	Dictionary containing the calculated metrics

		Examples:
			>>> # Prepare a test dataset
			>>> from .dataset import XyTuple
			>>> test_data = XyTuple(X=np.array([[1], [2], [3]]), y=np.array([0, 1, 0]))
			>>> dataset = Dataset(training_data=test_data, test_data=test_data, name="osef")

			>>> # Prepare predictions
			>>> predictions = np.array([[0.9, 0.1], [0.2, 0.8], [0.2, 0.8]])

			>>> # Calculate metrics
			>>> from stouputils.ctx import Muffle
			>>> with Muffle():
			... 	metrics = MetricUtils.metrics(dataset, predictions, run_name="")

			>>> # Check metrics
			>>> round(float(metrics[MetricDictionnary.ACCURACY]), 2)
			0.67
			>>> round(float(metrics[MetricDictionnary.PRECISION]), 2)
			0.5
			>>> round(float(metrics[MetricDictionnary.RECALL]), 2)
			1.0
			>>> round(float(metrics[MetricDictionnary.F1_SCORE]), 2)
			0.67
			>>> round(float(metrics[MetricDictionnary.AUC]), 2)
			0.75
			>>> round(float(metrics[MetricDictionnary.MATTHEWS_CORRELATION_COEFFICIENT]), 2)
			0.5
		"""
		# Initialize metrics
		metrics: dict[str, float] = {}
		y_true: NDArray[np.single] = dataset.test_data.ungrouped_array()[1]
		y_pred: NDArray[np.single] = np.array(predictions)

		# Binary classification
		if mode == "binary":
			true_classes: NDArray[np.intc] = Utils.convert_to_class_indices(y_true)
			pred_classes: NDArray[np.intc] = Utils.convert_to_class_indices(y_pred)

			# Get confusion matrix metrics
			conf_metrics: dict[str, float] = MetricUtils.confusion_matrix(
				true_classes=true_classes,
				pred_classes=pred_classes,
				labels=dataset.labels,
				run_name=run_name
			)
			metrics.update(conf_metrics)

			# Calculate F-beta scores
			precision: float = conf_metrics.get(MetricDictionnary.PRECISION, 0)
			recall: float = conf_metrics.get(MetricDictionnary.RECALL, 0)
			f_metrics: dict[str, float] = MetricUtils.f_scores(precision, recall)
			if f_metrics:
				metrics.update(f_metrics)

			# Calculate Matthews Correlation Coefficient
			mcc_metric: dict[str, float] = MetricUtils.matthews_correlation(true_classes, pred_classes)
			if mcc_metric:
				metrics.update(mcc_metric)

			# Calculate and plot ROC/AUC
			roc_metrics: dict[str, float] = MetricUtils.roc_and_auc(true_classes, y_pred, fold_number=-1, run_name=run_name)
			if roc_metrics:
				metrics.update(roc_metrics)

		# Multiclass classification
		elif mode == "multiclass":
			pass

		return metrics

	@staticmethod
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def confusion_matrix(
		true_classes: NDArray[np.intc],
		pred_classes: NDArray[np.intc],
		labels: tuple[str, ...],
		run_name: str = ""
	) -> dict[str, float]:
		""" Calculate metrics based on confusion matrix.

		Args:
			true_classes   (NDArray[np.intc]):  True class labels
			pred_classes   (NDArray[np.intc]):  Predicted class labels
			labels         (tuple[str, ...]):   List of class labels (strings)
			run_name       (str):               Name for saving the plot
		Returns:
			dict[str, float]:	Dictionary of confusion matrix based metrics

		Examples:
			>>> # Prepare data
			>>> true_classes = np.array([0, 1, 0])
			>>> pred_probs = np.array([[0.9, 0.1], [0.1, 0.9], [0.1, 0.9]])
			>>> pred_classes = Utils.convert_to_class_indices(pred_probs)	# [0, 1, 1]
			>>> labels = ["class_0", "class_1"]

			>>> # Calculate metrics
			>>> from stouputils.ctx import Muffle
			>>> with Muffle():
			... 	metrics = MetricUtils.confusion_matrix(true_classes, pred_classes, labels, run_name="")

			>>> # Check metrics
			>>> int(metrics[MetricDictionnary.CONFUSION_MATRIX_TN])
			1
			>>> int(metrics[MetricDictionnary.CONFUSION_MATRIX_FP])
			1
			>>> int(metrics[MetricDictionnary.CONFUSION_MATRIX_FN])
			0
			>>> int(metrics[MetricDictionnary.CONFUSION_MATRIX_TP])
			1
			>>> round(float(metrics[MetricDictionnary.FALSE_POSITIVE_RATE]), 2)
			0.5
		"""
		metrics: dict[str, float] = {}

		# Get basic confusion matrix values
		conf_matrix: NDArray[np.intc] = confusion_matrix(true_classes, pred_classes)
		TN: int = conf_matrix[0, 0]		# True Negatives
		FP: int = conf_matrix[0, 1]		# False Positives
		FN: int = conf_matrix[1, 0]		# False Negatives
		TP: int = conf_matrix[1, 1]		# True Positives

		# Calculate totals for each category
		total_samples: int				= TN + FP + FN + TP
		total_actual_negatives: int		= TN + FP
		total_actual_positives: int		= TP + FN
		total_predicted_negatives: int	= TN + FN
		total_predicted_positives: int	= TP + FP

		# Calculate core metrics
		specificity: float =        Utils.safe_divide_float(TN, total_actual_negatives)
		recall: float =             Utils.safe_divide_float(TP, total_actual_positives)
		precision: float =          Utils.safe_divide_float(TP, total_predicted_positives)
		npv: float =                Utils.safe_divide_float(TN, total_predicted_negatives)
		accuracy: float =           Utils.safe_divide_float(TN + TP, total_samples)
		balanced_accuracy: float =  (specificity + recall) / 2
		f1_score: float =           Utils.safe_divide_float(2 * (precision * recall), precision + recall)
		f1_score_negative: float =  Utils.safe_divide_float(2 * (specificity * npv), specificity + npv)

		# Store main metrics using MetricDictionnary
		metrics[MetricDictionnary.SPECIFICITY] = specificity
		metrics[MetricDictionnary.RECALL] = recall
		metrics[MetricDictionnary.PRECISION] = precision
		metrics[MetricDictionnary.NPV] = npv
		metrics[MetricDictionnary.ACCURACY] = accuracy
		metrics[MetricDictionnary.BALANCED_ACCURACY] = balanced_accuracy
		metrics[MetricDictionnary.F1_SCORE] = f1_score
		metrics[MetricDictionnary.F1_SCORE_NEGATIVE] = f1_score_negative

		# Store confusion matrix values and derived metrics
		metrics[MetricDictionnary.CONFUSION_MATRIX_TN] = TN
		metrics[MetricDictionnary.CONFUSION_MATRIX_FP] = FP
		metrics[MetricDictionnary.CONFUSION_MATRIX_FN] = FN
		metrics[MetricDictionnary.CONFUSION_MATRIX_TP] = TP
		metrics[MetricDictionnary.FALSE_POSITIVE_RATE] = Utils.safe_divide_float(FP, total_actual_negatives)
		metrics[MetricDictionnary.FALSE_NEGATIVE_RATE] = Utils.safe_divide_float(FN, total_actual_positives)
		metrics[MetricDictionnary.FALSE_DISCOVERY_RATE] = Utils.safe_divide_float(FP, total_predicted_positives)
		metrics[MetricDictionnary.FALSE_OMISSION_RATE] = Utils.safe_divide_float(FN, total_predicted_negatives)
		metrics[MetricDictionnary.CRITICAL_SUCCESS_INDEX] = Utils.safe_divide_float(TP, total_actual_positives + FP)

		# Plot confusion matrix
		if run_name:
			confusion_matrix_path: str = f"{DataScienceConfig.TEMP_FOLDER}/{run_name}_confusion_matrix.png"
			ConfusionMatrixDisplay.from_predictions(true_classes, pred_classes, display_labels=labels)
			plt.savefig(confusion_matrix_path)
			mlflow.log_artifact(confusion_matrix_path)
			os.remove(confusion_matrix_path)
		plt.close()

		return metrics

	@staticmethod
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def f_scores(precision: float, recall: float) -> dict[str, float]:
		""" Calculate F-beta scores for different beta values.

		Args:
			precision	(float):	Precision value
			recall		(float):	Recall value
		Returns:
			dict[str, float]:	Dictionary of F-beta scores

		Examples:
			>>> from stouputils.ctx import Muffle
			>>> with Muffle():
			... 	metrics = MetricUtils.f_scores(precision=0.5, recall=1.0)
			>>> [round(float(x), 2) for x in metrics.values()]
			[0.5, 0.51, 0.54, 0.58, 0.62, 0.67, 0.71, 0.75, 0.78, 0.81, 0.83]

		"""
		# Assertions
		assert precision > 0, "Precision cannot be 0"
		assert recall > 0, "Recall cannot be 0"

		# Calculate F-beta scores
		metrics: dict[str, float] = {}
		betas: Iterable[float] = np.linspace(0, 2, 11)
		for beta in betas:
			divider: float = (beta**2 * precision) + recall
			score: float = Utils.safe_divide_float((1 + beta**2) * precision * recall, divider)
			metrics[MetricDictionnary.F_SCORE_X.replace("X", f"{beta:.1f}")] = score
			if score == 0:
				warning(f"F-score is 0 for beta={beta:.1f}")
		return metrics

	@staticmethod
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def matthews_correlation(true_classes: NDArray[np.intc], pred_classes: NDArray[np.intc]) -> dict[str, float]:
		""" Calculate Matthews Correlation Coefficient.

		Args:
			true_classes	(NDArray[np.intc]):	True class labels
			pred_classes	(NDArray[np.intc]):	Predicted class labels
		Returns:
			dict[str, float]:	Dictionary containing MCC

		Examples:
			>>> true_classes = np.array([0, 1, 0])
			>>> pred_classes = np.array([0, 1, 1])
			>>> from stouputils.ctx import Muffle
			>>> with Muffle():
			... 	metrics = MetricUtils.matthews_correlation(true_classes, pred_classes)
			>>> float(metrics[MetricDictionnary.MATTHEWS_CORRELATION_COEFFICIENT])
			0.5
		"""
		return {MetricDictionnary.MATTHEWS_CORRELATION_COEFFICIENT: matthews_corrcoef(true_classes, pred_classes)}


	@staticmethod
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def roc_and_auc(
		true_classes: NDArray[np.intc] | NDArray[np.single],
		pred_probs: NDArray[np.single],
		fold_number: int = -1,
		run_name: str = ""
	) -> dict[str, float]:
		""" Calculate ROC curve and AUC score.

		Args:
			true_classes  (NDArray[np.intc | np.single]):  True class labels (one-hot encoded or class indices)
			pred_probs    (NDArray[np.single]):            Predicted probabilities (must be probability scores, not class indices)
			fold_number   (int):                           Fold number, used for naming the plot file, usually
				-1 for final model with test set,
				0 for final model with validation set,
				>0 for other folds with their validation set
			run_name      (str):                           Name for saving the plot
		Returns:
			dict[str, float]:	Dictionary containing AUC score and optimal thresholds

		Examples:
			>>> true_classes = np.array([0, 1, 0])
			>>> pred_probs = np.array([[0.9, 0.1], [0.1, 0.9], [0.1, 0.9]])
			>>> from stouputils.ctx import Muffle
			>>> with Muffle():
			... 	metrics = MetricUtils.roc_and_auc(true_classes, pred_probs, run_name="")

			>>> # Check metrics
			>>> round(float(metrics[MetricDictionnary.AUC]), 2)
			0.75
			>>> round(float(metrics[MetricDictionnary.OPTIMAL_THRESHOLD_YOUDEN]), 2)
			0.9
			>>> float(metrics[MetricDictionnary.OPTIMAL_THRESHOLD_COST])
			inf
		"""
		true_classes = Utils.convert_to_class_indices(true_classes)
		auc_value, fpr, tpr, thresholds = Utils.get_roc_curve_and_auc(true_classes, pred_probs)
		metrics: dict[str, float] = {MetricDictionnary.AUC: auc_value}

		# Find optimal threshold using different methods
		# 1. Youden's method
		youden_index: NDArray[np.single] = tpr - fpr
		optimal_threshold_youden: float = thresholds[np.argmax(youden_index)]
		metrics[MetricDictionnary.OPTIMAL_THRESHOLD_YOUDEN] = optimal_threshold_youden

		# 2. Cost-based method
		# Assuming false positives cost twice as much as false negatives
		cost_fp: float = 2
		cost_fn: float = 1
		total_cost: NDArray[np.single] = cost_fp * fpr + cost_fn * (1 - tpr)
		optimal_threshold_cost: float = thresholds[np.argmin(total_cost)]
		metrics[MetricDictionnary.OPTIMAL_THRESHOLD_COST] = optimal_threshold_cost

		# Plot ROC curve if not nan
		if run_name and not np.isnan(auc_value):
			plt.figure(figsize=(12, 6))
			plt.plot(fpr, tpr, "b", label=f"ROC curve (AUC = {auc_value:.2f})")
			plt.plot([0, 1], [0, 1], "r--")

			# Add optimal threshold points
			youden_idx: int = int(np.argmax(youden_index))
			cost_idx: int = int(np.argmin(total_cost))

			# Prepare the path
			fold_name: str = ""
			if fold_number > 0:
				fold_name = f"_fold_{fold_number}_val"
			elif fold_number == 0:
				fold_name = "_val"
			elif fold_number == -1:
				fold_name = "_test"
			elif fold_number == -2:
				fold_name = "_train"
			roc_curve_path: str = f"{DataScienceConfig.TEMP_FOLDER}/{run_name}_roc_curve{fold_name}.png"

			plt.plot(fpr[youden_idx], tpr[youden_idx], 'go', label=f'Youden (t={optimal_threshold_youden:.2f})')
			plt.plot(fpr[cost_idx], tpr[cost_idx], 'mo', label=f'Cost (t={optimal_threshold_cost:.2f})')

			plt.xlim([-0.01, 1.01])
			plt.ylim([-0.01, 1.01])
			plt.xlabel("False Positive Rate")
			plt.ylabel("True Positive Rate")
			plt.title("Receiver Operating Characteristic (ROC)")
			plt.legend(loc="lower right")
			plt.savefig(roc_curve_path)
			mlflow.log_artifact(roc_curve_path)
			os.remove(roc_curve_path)
			plt.close()

		return metrics


	@staticmethod
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def plot_metric_curves(
		all_history: list[dict[str, list[float]]],
		metric_name: str,
		run_name: str = ""
	) -> None:
		""" Plot training and validation curves for a specific metric.

		Generates two plots for the given metric:
		1. A combined plot with both training and validation curves
		2. A validation-only plot

		The plots show the metric's progression across training epochs for each fold.
		Special formatting distinguishes between folds and curve types:
		- Fold 0 (final model) uses thicker lines (2.0 width vs 1.0)
		- Training curves use solid lines, validation uses dashed
		- Each curve is clearly labeled in the legend

		The plots are saved to the temp folder and logged to MLflow before cleanup.

		Args:
			all_history (list[dict[str, list[float]]]):    List of history dictionaries for each fold
			metric_name (str):                             Name of the metric to plot (e.g. "accuracy", "loss")
			run_name    (str):                             Name of the run

		Examples:
			>>> # Prepare data with 2 folds for instance
			>>> all_history = [
			... 	{'loss': [0.1, 0.09, 0.08, 0.07, 0.06], 'val_loss': [0.11, 0.1, 0.09, 0.08, 0.07]},
			... 	{'loss': [0.12, 0.11, 0.1, 0.09, 0.08], 'val_loss': [0.13, 0.12, 0.11, 0.1, 0.09]}
			... ]
			>>> MetricUtils.plot_metric_curves(metric_name="loss", all_history=all_history, run_name="")
		"""
		for only_validation in (False, True):
			plt.figure(figsize=(12, 6))

			# Track max value for y-limit calculation
			max_value: float = 0.0

			for fold, history in enumerate(all_history):
				# Get validation metrics for this fold
				val_metric: list[float] = history[f"val_{metric_name}"]
				epochs: list[int] = list(range(1, len(val_metric) + 1))

				# Update max value
				max_value = max(max_value, max(val_metric))

				# Use thicker line for final model (fold 0)
				alpha: float = 1.0 if fold == 0 else 0.5
				linewidth: float = 2.0 if fold == 0 else 1.0
				label: str = "Final Model" if fold == 0 else f"Fold {fold + 1}"
				val_label: str = f"Validation {metric_name} ({label})"
				plt.plot(epochs, val_metric, linestyle='--', linewidth=linewidth, alpha=alpha, label=val_label)

				# Add training metrics if showing both curves
				if not only_validation:
					train_metric: list[float] = history[metric_name]
					max_value = max(max_value, max(train_metric))
					train_label: str = f"Training {metric_name} ({label})"
					plt.plot(epochs, train_metric, linestyle='-', linewidth=linewidth, alpha=alpha, label=train_label)

			# Configure plot formatting
			plt.title(("Training and " if not only_validation else "") + f"Validation {metric_name} Across All Folds")
			plt.xlabel("Epochs")
			plt.ylabel(metric_name)

			# Set y-limit for loss metric, to avoid seeing non-sense curves
			if metric_name == "loss" and not only_validation:
				plt.ylim(0, min(2.0, max_value * 1.1))

			# Add legend
			plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
			plt.tight_layout()

			# Save plot and log to MLflow
			if run_name:
				path: str = ("training_" if not only_validation else "") + f"validation_{metric_name}_curves.png"
				full_path: str = f"{DataScienceConfig.TEMP_FOLDER}/{run_name}_{path}"
				plt.savefig(full_path, bbox_inches='tight')
				mlflow.log_artifact(full_path)
				os.remove(full_path)
			plt.close()

	@staticmethod
	def plot_every_metric_curves(
		all_history: list[dict[str, list[float]]],
		metrics_names: tuple[str, ...] = (),
		run_name: str = ""
	) -> None:
		""" Plot and save training and validation curves for each metric.

		Args:
			all_history     (list[dict[str, list[float]]]): List of history dictionaries for each fold
			metrics_names   (tuple[str, ...]):              List of metric names to plot, defaults to ("loss",)
			run_name        (str):                          Name of the run

		Examples:
			>>> # Prepare data with 2 folds for instance
			>>> all_history = [
			... 	{'loss': [0.1, 0.09], 'val_loss': [0.11, 0.1], "accuracy": [0.9, 0.8], "val_accuracy": [0.8, 0.7]},
			... 	{'loss': [0.12, 0.11], 'val_loss': [0.13, 0.12], "accuracy": [0.8, 0.7], "val_accuracy": [0.7, 0.6]}
			... ]
			>>> MetricUtils.plot_every_metric_curves(all_history, metrics_names=["loss", "accuracy"], run_name="")
		"""
		# Set default metrics names to loss
		if not metrics_names:
			metrics_names = ("loss",)

		# Plot each metric
		for metric_name in metrics_names:
			MetricUtils.plot_metric_curves(all_history, metric_name, run_name)

	@staticmethod
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def find_best_x_and_plot(
		x_values: list[float],
		y_values: list[float],
		best_idx: int | None = None,
		smoothen: bool = True,
		use_steep: bool = True,
		run_name: str = "",
		x_label: str = "Learning Rate",
		y_label: str = "Loss",
		plot_title: str = "Learning Rate Finder",
		log_x: bool = True,
		y_limits: tuple[float, ...] | None = None
	) -> float:
		""" Find the best x value (where y is minimized) and plot the curve.

		Args:
			x_values    (list[float]):               List of x values (e.g. learning rates)
			y_values    (list[float]):               List of corresponding y values (e.g. losses)
			best_idx    (int | None):                Index of the best x value (if None, a robust approach is used)
			smoothen    (bool):                      Whether to apply smoothing to the y values
			use_steep   (bool):                      Whether to use steepest slope strategy to determine best index
			run_name    (str):                       Name of the run for saving the plot
			x_label     (str):                       Label for the x-axis
			y_label     (str):                       Label for the y-axis
			plot_title  (str):                       Title for the plot
			log_x       (bool):                      Whether to use a logarithmic x-axis (e.g. learning rate)
			y_limits    (tuple[float, ...] | None):  Limit for the y-axis, defaults to None (no limit)

		Returns:
			float: The best x value found (where y is minimized)

		This function creates a plot showing the relationship between x and y values
		to help identify the optimal x (where y is minimized). The plot can use a logarithmic
		x-axis for better visualization if desired.

		The ideal x is typically found where y is still decreasing but before it starts to increase dramatically.

		Examples:
			>>> x_values = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]
			>>> y_values = [0.1, 0.09, 0.07, 0.06, 0.09]
			>>> best_x = MetricUtils.find_best_x_and_plot(x_values, y_values, use_steep=True)
			>>> print(f"Best x: {best_x:.0e}")
			Best x: 1e-03
			>>> best_x = MetricUtils.find_best_x_and_plot(x_values, y_values, use_steep=False)
			>>> print(f"Best x: {best_x:.0e}")
			Best x: 1e-02
		"""
		# Validate input data
		assert x_values, "No x data to plot"
		assert y_values, "No y data to plot"

		# Convert lists to numpy arrays for easier manipulation
		y_array: NDArray[np.single] = np.array(y_values)
		x_array: NDArray[np.single] = np.array(x_values)

		# Apply smoothing to the y values if requested and if we have enough data points
		if smoothen and len(y_values) > 2:

			# Calculate appropriate window size based on data length
			window_size: int = min(10, len(y_values) // 3)
			if window_size > 1:

				# Apply moving average smoothing using convolution
				valid_convolution: NDArray[np.single] = np.convolve(y_array, np.ones(window_size)/window_size, mode="valid")
				y_array = np.copy(y_array)

				# Calculate start and end indices for replacing values with smoothed ones
				start_idx: int = window_size // 2
				end_idx: int = start_idx + len(valid_convolution)
				y_array[start_idx:end_idx] = valid_convolution

				# Replace first and last values with original values (to avoid weird effects)
				y_array[0] = y_values[0]
				y_array[-1] = y_values[-1]

		# 1. Global minimum index between 10% and 90% (excluding borders)
		window_start: int = int(0.1 * len(y_array))
		window_end: int = int(0.9 * len(y_array))
		global_window_min_idx: int = int(np.argmin(y_array[window_start:window_end]))
		global_min_idx: int = global_window_min_idx + window_start

		# Determine best index
		if best_idx is None:
			if use_steep:

				# 2. Compute slope in loss vs log(x) for LR sensitivity
				log_x_array: NDArray[np.single] = np.log(x_array)
				slopes: NDArray[np.single] = np.gradient(y_array, log_x_array)

				# 3. Define proximity window to the left of global minimum
				proximity: int = max(1, len(y_array) // 10)
				window_start = max(0, global_min_idx - proximity)

				# 4. Find steepest slope within window
				if window_start < global_min_idx:
					local_slopes: NDArray[np.single] = slopes[window_start:global_min_idx]
					relative_idx: int = int(np.argmin(local_slopes))
					steep_idx: int = window_start + relative_idx
					best_idx = steep_idx
				else:
					best_idx = global_min_idx

				# 5. Top-7 most negative slopes as candidates
				neg_idx: NDArray[np.intp] = np.where(slopes < 0)[0]
				sorted_neg: NDArray[np.intp] = neg_idx[np.argsort(slopes[neg_idx])]
				top7_fave: NDArray[np.intp] = sorted_neg[:7]

				# Include best_idx and global_min_idx
				candidates: set[int] = set(top7_fave.tolist())
				candidates.add(best_idx)
				distinct_candidates = np.array(sorted(candidates, key=int))
			else:
				best_idx = global_min_idx

				# Find all local minima
				from scipy.signal import argrelextrema
				local_minima_idx: NDArray[np.intp] = argrelextrema(y_array, np.less)[0]
				distinct_candidates = np.unique(np.append(local_minima_idx, best_idx))
		else:
			assert 0 <= best_idx < len(x_array), "Best x index is out of bounds"
			distinct_candidates = np.array([best_idx])

		# Get the best x value and corresponding y value
		best_x: float = x_array[best_idx]
		min_y: float = y_array[best_idx]

		# Create and save the plot if a run name is provided
		if run_name:

			# Log metrics to mlflow (e.g. 'learning_rate_finder_learning_rate', 'learning_rate_finder_loss')
			log_title: str = MetricDictionnary.PARAMETER_FINDER.replace("TITLE", plot_title)
			log_x_label: str = log_title.replace("PARAMETER_NAME", x_label)
			log_y_label: str = log_title.replace("PARAMETER_NAME", y_label)
			for i in range(len(x_values)):
				mlflow.log_metric(log_x_label, x_values[i], step=i)
				mlflow.log_metric(log_y_label, y_values[i], step=i)

			# Prepare the plot
			plt.figure(figsize=(12, 6))
			plt.plot(x_array, y_array, label="Smoothed Curve", linewidth=2)
			plt.plot(x_values, y_values, "-", markersize=3, alpha=0.5, label="Original Curve", color="gray")

			# Use logarithmic scale for x-axis if requested
			if log_x:
				plt.xscale("log")

			# Set labels and title
			plt.xlabel(x_label)
			plt.ylabel(y_label)
			plt.title(plot_title)
			plt.grid(True, which="both", ls="--")

			# Limit y-axis to avoid extreme values
			if y_limits is not None and len(y_limits) == 2:
				min_y_limit: float = max(y_limits[0], min(y_values) * 0.9)
				max_y_limit: float = min(y_limits[1], max(y_values) * 1.1)
				plt.ylim(min_y_limit, max_y_limit)
			plt.legend()

			# Highlight local minima if any
			if len(distinct_candidates) > 0:
				candidate_xs = [x_array[idx] for idx in distinct_candidates]
				candidate_ys = [y_array[idx] for idx in distinct_candidates]
				candidates_label = "Possible Candidates" if use_steep else "Local Minima"
				plt.scatter(candidate_xs, candidate_ys, color="orange", s=25, zorder=4, label=candidates_label)

			# Highlight the best point
			plt.scatter([x_array[global_min_idx]], [y_array[global_min_idx]], color="red", s=50, zorder=5, label="Global Minimum")

			# Format the best x value for display
			best_x_str: str = f"{best_x:.2e}" if best_x < 1e-3 else f"{best_x:.2f}"

			# Add annotation pointing to the best point
			plt.annotate(
				f"Supposed best {x_label}: {best_x_str}",
				xy=(best_x, min_y),
				xytext=(best_x * 1.5, min_y * 1.1),
				arrowprops={"facecolor":"black", "shrink":0.05, "width":1.2}
			)
			plt.legend()
			plt.tight_layout()

			# Save the plot to a file and log it to MLflow
			flat_x_label: str = x_label.lower().replace(" ", "_")
			path: str = f"{flat_x_label}_finder.png"
			os.makedirs(DataScienceConfig.TEMP_FOLDER, exist_ok=True)
			full_path: str = f"{DataScienceConfig.TEMP_FOLDER}/{run_name}_{path}"
			plt.savefig(full_path, bbox_inches="tight")
			mlflow.log_artifact(full_path)
			info(f"Saved best x plot to {full_path}")

			# Clean up the temporary file
			os.remove(full_path)
			plt.close()

		return best_x

