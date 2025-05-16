"""
This module contains the MetricDictionnary class, which provides a dictionary of metric names.

This is often used to log metrics to MLflow and to display them in the console easily.

This class contains the following metrics:

1. Main metrics:

   - Area Under the Curve (AUC)
   - Specificity (True Negative Rate)
   - Recall/Sensitivity (True Positive Rate)
   - Precision (Positive Predictive Value)
   - Negative Predictive Value (NPV)
   - Accuracy
   - F1 Score

2. Confusion matrix metrics:

   - True Negatives (TN)
   - False Positives (FP)
   - False Negatives (FN)
   - True Positives (TP)
   - False Positive Rate
   - False Negative Rate
   - False Discovery Rate
   - False Omission Rate
   - Critical Success Index (Threat Score)

3. F-scores:

   - F-beta Score (where beta is configurable)

4. Matthews correlation coefficient:

   - Matthews Correlation Coefficient (MCC)

5. Optimal thresholds for binary classification:

   - Youden's J statistic
   - Cost-based threshold

6. Average metrics across folds:

   - Mean value of any metric across k-fold cross validation

7. Standard deviation metrics across folds:

   - Standard deviation of any metric across k-fold cross validation
"""

class MetricDictionnary:

	# Main metrics (starting with '1:')
	AUC: str								= "1: Area Under the Curve: AUC"
	SPECIFICITY: str						= "1: Specificity: True Negative Rate"
	RECALL: str								= "1: Recall/Sensitivity: True Positive Rate"
	PRECISION: str							= "1: Precision: Positive Predictive Value"
	NPV: str								= "1: NPV: Negative Predictive Value"
	ACCURACY: str							= "1: Accuracy"
	BALANCED_ACCURACY: str					= "1: Balanced Accuracy"
	F1_SCORE: str							= "1: F1 Score"
	F1_SCORE_NEGATIVE: str					= "1: F1 Score for Negative Class"

	# Confusion matrix metrics (starting with '2:')
	CONFUSION_MATRIX_TN: str				= "2: Confusion Matrix: TN"
	CONFUSION_MATRIX_FP: str				= "2: Confusion Matrix: FP"
	CONFUSION_MATRIX_FN: str				= "2: Confusion Matrix: FN"
	CONFUSION_MATRIX_TP: str				= "2: Confusion Matrix: TP"
	FALSE_POSITIVE_RATE: str				= "2: False Positive Rate"
	FALSE_NEGATIVE_RATE: str				= "2: False Negative Rate"
	FALSE_DISCOVERY_RATE: str				= "2: False Discovery Rate"
	FALSE_OMISSION_RATE: str				= "2: False Omission Rate"
	CRITICAL_SUCCESS_INDEX: str				= "2: Critical Success Index: Threat Score"

	# F-scores (starting with '3:')
	F_SCORE_X: str							= "3: F-X Score"	# X is the beta value

	# Matthews correlation coefficient (starting with '4:')
	MATTHEWS_CORRELATION_COEFFICIENT: str	= "4: Matthews Correlation Coefficient: MCC"

	# Optimal thresholds (starting with '5:')
	OPTIMAL_THRESHOLD_YOUDEN: str			= "5: Optimal Threshold: Youden"
	OPTIMAL_THRESHOLD_COST: str				= "5: Optimal Threshold: Cost"

	# Average metrics across folds (starting with '6:')
	AVERAGE_METRIC: str						= "6: Average METRIC_NAME across folds"

	# Standard deviation metrics across folds (starting with '7:')
	STANDARD_DEVIATION_METRIC: str			= "7: Standard deviation METRIC_NAME across folds"

	# Parameter finder (starting with '8:')
	PARAMETER_FINDER: str					= "8: TITLE: PARAMETER_NAME"

