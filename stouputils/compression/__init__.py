"""
This module provides lossy compressors for the series a long-running job writes far more often than anyone reads back:

- :py:class:`~deadband.DeadbandFilter` - Thin a curve down to the points the line drawn through it cannot be read off without
- :py:class:`~deadband.MetricCurve` - What one key has written so far, and the span of points it is holding back

.. code-block:: python

	import math
	import stouputils as stp

	deadband = stp.DeadbandFilter()
	points_written = {"loss": 0, "lr": 0}

	# The filter hands back only the points needed to redraw each curve, here we count them
	def count(kept_points: dict[int, dict[str, float]]) -> None:
		for metrics in kept_points.values():
			for name in metrics:
				points_written[name] += 1

	# 1000 training steps: a loss that slowly decays and a learning rate that drops once
	for step in range(1000):
		learning_rate = 0.1 if step < 500 else 0.01
		count(deadband.feed({"loss": math.exp(-step / 200), "lr": learning_rate}, step))

	# At the end of the run, release the points the filter still holds back
	count(deadband.flush())
	stp.info("Points written out of 1000 per curve:", points_written)

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/compression_module.svg
  :alt: Terminal output of the example, the few points kept per curve
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

