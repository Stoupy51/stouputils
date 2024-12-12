
# Imports
from multiprocessing import Pool
from typing import Callable, Iterable, Literal
from matplotlib import pyplot as plt
import numpy as np
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix, roc_curve, auc, matthews_corrcoef
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
from .config import *
from .print import *
from .dataset import Dataset
import mlflow


# Small test functions for doctests
def doctest_square(x: int) -> int:
	return x * x
def doctest_multiply(args) -> int:
	x, y = args
	return x * y
def doctest_slow(x: int) -> int:
	import time
	time.sleep(0.1)
	return x


# Class
class Utils(object):
	BAR_FORMAT: str = "{l_bar}{bar}" + MAGENTA + "| {n_fmt}/{total_fmt} [{rate_fmt}{postfix}]" + RESET

	@staticmethod
	@handle_error(error_log=4)
	def multiprocessing(func: Callable, args: list, chunksize: int = 1, desc: str = "", max_workers: int = CPU_COUNT, verbose_depth: int = 0) -> list[object]:
		""" Method to execute a function in parallel using multiprocessing.\n
		Args:
			func			(Callable):			Function to execute
			args			(list):				List of arguments to pass to the function (no starmap will be used)
			chunksize		(int):				Number of arguments to process at a time (Defaults to 1 for proper progress bar display)
			desc			(str):				Description of the function execution displayed in the progress bar
			max_workers		(int):				Number of workers to use (Defaults to CPU_COUNT)
			verbose_depth	(int):				Level of verbosity, decrease by 1 for each depth
		Returns:
			list[object]:	Results of the function execution
		Examples:
			>>> Utils.multiprocessing(doctest_square, args=[1, 2, 3])
			[1, 4, 9]

			>>> Utils.multiprocessing(doctest_multiply, [(1,2), (3,4), (5,6)])
			[2, 12, 30]

			>>> # Will process in parallel with progress bar
			>>> Utils.multiprocessing(doctest_slow, list(range(10)), desc="Processing", max_workers=2, verbose_depth=1)
			[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
		"""
		if desc:
			desc = MAGENTA + desc

		# Do multiprocessing only if there is more than 1 argument and more than 1 CPU
		if max_workers > 1 and len(args) > 1:
			if verbose_depth > 0:
				return list(process_map(func, args, max_workers=max_workers, chunksize=chunksize, desc=desc, bar_format=Utils.BAR_FORMAT))
			else:
				with Pool(max_workers) as pool:
					return list(pool.map(func, args, chunksize=chunksize))

		# Single process execution
		else:
			if verbose_depth > 0:
				return list(tqdm(args, total=len(args), desc=desc, bar_format=Utils.BAR_FORMAT))
			else:
				return [func(arg) for arg in args]

	@staticmethod
	@measure_time(info, "Execution time of Utils.metrics")
	@handle_error(error_log=ERROR_LOG)
	def metrics(dataset: Dataset, predictions: Iterable, run_name: str, mode: Literal["binary", "multiclass", "none"] = "binary") -> dict[str, float]:
		""" Method to calculate as many metrics as possible for the given dataset and predictions.\n
		Args:
			dataset		(Dataset):		Dataset containing the true labels
			predictions	(Iterable):		Predictions made by the model
			run_name	(str):			Name of the run, used to save the ROC curve
			mode		(Literal):		Mode of the classification, defaults to "binary"
		Returns:
			dict[str, float]:	Dictionary containing the calculated metrics
		"""
		# Initialize metrics
		metrics: dict[str, float] = {}
		y_true: np.ndarray = dataset.test_data.y
		y_pred: np.ndarray = np.array(predictions)

		# Binary classification
		if mode == "binary":
			true_classes: np.ndarray = np.argmax(y_true, axis=1)
			pred_classes: np.ndarray = np.argmax(y_pred, axis=1)

			# Get confusion matrix metrics
			conf_metrics: dict[str, float] = Utils.confusion_matrix(true_classes, pred_classes, run_name)
			metrics.update(conf_metrics)

			# Calculate F-beta scores
			precision: float = conf_metrics.get("_Precision: Positive Predictive Value", 0)
			recall: float = conf_metrics.get("_Recall/Sensitivity: True Positive Rate", 0)
			f_metrics: dict[str, float] = Utils.f_scores(precision, recall)
			if f_metrics:
				metrics.update(f_metrics)

			# Calculate Matthews Correlation Coefficient
			mcc_metric: dict[str, float] = Utils.matthews_correlation(true_classes, pred_classes)
			if mcc_metric:
				metrics.update(mcc_metric)

			# Calculate and plot ROC/AUC
			roc_metrics: dict[str, float] = Utils.roc_and_auc(true_classes, pred_classes, run_name)
			if roc_metrics:
				metrics.update(roc_metrics)

		# Multiclass classification
		elif mode == "multiclass":
			pass

		return metrics

	@staticmethod
	@measure_time(debug, "Execution time of Utils.confusion_matrix")
	@handle_error(error_log=ERROR_LOG)
	def confusion_matrix(true_classes: np.ndarray, pred_classes: np.ndarray, run_name: str) -> dict[str, float]:
		"""Calculate metrics based on confusion matrix.\n
		Args:
			true_classes	(np.ndarray):	True class labels
			pred_classes	(np.ndarray):	Predicted class labels
			run_name		(str):			Name for saving the plot
		Returns:
			dict[str, float]:	Dictionary of confusion matrix based metrics
		"""
		metrics: dict[str, float] = {}
		
		# Get basic confusion matrix values
		conf_matrix: np.ndarray = confusion_matrix(true_classes, pred_classes)
		true_negatives: int = conf_matrix[0, 0]
		false_positives: int = conf_matrix[0, 1]
		false_negatives: int = conf_matrix[1, 0]
		true_positives: int = conf_matrix[1, 1]

		# Calculate totals for each category
		total_samples: int				= true_negatives + false_positives + false_negatives + true_positives
		total_actual_negatives: int		= true_negatives + false_positives
		total_actual_positives: int		= true_positives + false_negatives
		total_predicted_negatives: int	= true_negatives + false_negatives
		total_predicted_positives: int	= true_positives + false_positives

		# Calculate core metrics
		specificity: float	= true_negatives / total_actual_negatives if total_actual_negatives > 0 else 0
		recall: float		= true_positives / total_actual_positives if total_actual_positives > 0 else 0
		precision: float	= true_positives / total_predicted_positives if total_predicted_positives > 0 else 0
		accuracy: float		= (true_negatives + true_positives) / total_samples
		f1_score: float		= 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

		# Store main metrics (starting with underscore for easy sorting)
		metrics["1: Specificity: True Negative Rate"] = specificity
		metrics["1: Recall/Sensitivity: True Positive Rate"] = recall
		metrics["1: Precision: Positive Predictive Value"] = precision
		metrics["1: Accuracy"] = accuracy
		metrics["1: F1 Score"] = f1_score

		# Store confusion matrix values and derived metrics
		metrics["2: Confusion Matrix: TN"] = true_negatives
		metrics["2: Confusion Matrix: FP"] = false_positives
		metrics["2: Confusion Matrix: FN"] = false_negatives
		metrics["2: Confusion Matrix: TP"] = true_positives
		metrics["2: False Positive Rate"] = false_positives / total_actual_negatives if total_actual_negatives > 0 else 0
		metrics["2: False Negative Rate"] = false_negatives / total_actual_positives if total_actual_positives > 0 else 0
		metrics["2: Negative Predictive Value"] = true_negatives / total_predicted_negatives if total_predicted_negatives > 0 else 0
		metrics["2: False Discovery Rate"] = false_positives / total_predicted_positives if total_predicted_positives > 0 else 0
		metrics["2: False Omission Rate"] = false_negatives / total_predicted_negatives if total_predicted_negatives > 0 else 0
		metrics["2: Threat Score: Critical Success Index"] = true_positives / (total_actual_positives + false_positives) if (total_actual_positives + false_positives) > 0 else 0

		# Plot confusion matrix
		confusion_matrix_path: str = f"{run_name}_confusion_matrix.png"
		ConfusionMatrixDisplay.from_predictions(true_classes, pred_classes)
		plt.savefig(confusion_matrix_path)
		plt.close()
		mlflow.log_artifact(confusion_matrix_path)
		os.remove(confusion_matrix_path)

		return metrics

	@staticmethod
	@measure_time(debug, "Execution time of Utils.f_scores")
	@handle_error(error_log=ERROR_LOG)
	def f_scores(precision: float, recall: float) -> dict[str, float]:
		"""Calculate F-beta scores for different beta values.\n
		Args:
			precision	(float):	Precision value
			recall		(float):	Recall value
		Returns:
			dict[str, float]:	Dictionary of F-beta scores
		"""
		metrics: dict[str, float] = {}
		betas: Iterable[float] = np.linspace(0, 2, 11)
		for beta in betas:
			divider: float = (beta**2 * precision) + recall
			metrics[f"3: F Score: {beta:.1f}"] = ((1 + beta**2) * precision * recall) / divider if divider > 0 else 0
		return metrics

	@staticmethod
	@measure_time(debug, "Execution time of Utils.matthews_correlation")
	@handle_error(error_log=ERROR_LOG)
	def matthews_correlation(true_classes: np.ndarray, pred_classes: np.ndarray) -> dict[str, float]:
		"""Calculate Matthews Correlation Coefficient.\n
		Args:
			true_classes	(np.ndarray):	True class labels
			pred_classes	(np.ndarray):	Predicted class labels
		Returns:
			dict[str, float]:	Dictionary containing MCC
		"""
		return {"2: Matthews Correlation Coefficient: MCC": matthews_corrcoef(true_classes, pred_classes)}

	@staticmethod
	@measure_time(debug, "Execution time of Utils.roc_and_auc")
	@handle_error(error_log=ERROR_LOG)
	def roc_and_auc(true_classes: np.ndarray, pred_classes: np.ndarray, run_name: str) -> dict[str, float]:
		"""Calculate ROC curve and AUC score.\n
		Args:
			true_classes	(np.ndarray):	True class labels
			pred_classes	(np.ndarray):	Predicted class labels
			run_name	(str):			Name for saving the plot
		Returns:
			dict[str, float]:	Dictionary containing AUC score
		"""
		fpr, tpr, _ = roc_curve(true_classes, pred_classes)
		auc_value: float = float(auc(fpr, tpr))

		plt.figure(figsize=(12, 6))
		plt.plot(fpr, tpr, "b", label=f"ROC curve (AUC = {auc_value:.2f})")
		plt.plot([0, 1], [0, 1], "r--")
		plt.xlim([0, 1])
		plt.ylim([0, 1])
		plt.xlabel("False Positive Rate")
		plt.ylabel("True Positive Rate")
		plt.title("Receiver Operating Characteristic (ROC)")
		plt.legend(loc="lower right")
		roc_curve_path: str = f"{run_name}_roc_curve.png"
		plt.savefig(roc_curve_path)
		plt.close()
		mlflow.log_artifact(roc_curve_path)
		os.remove(roc_curve_path)

		return {"1: Area Under the Curve: AUC": auc_value}

