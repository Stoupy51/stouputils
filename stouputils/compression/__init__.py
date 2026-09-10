"""
This module provides lossy compressors for the series a long-running job writes far more often than anyone reads back:

- :py:class:`~deadband.DeadbandFilter` - Thin a curve down to the points the line drawn through it cannot be read off without
- :py:class:`~deadband.MetricCurve` - What one key has written so far, and the span of points it is holding back
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .deadband import (
	METRIC_DEADBAND as METRIC_DEADBAND,
	DeadbandFilter as DeadbandFilter,
	MetricCurve as MetricCurve,
)
