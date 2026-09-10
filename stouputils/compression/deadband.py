""" Deadband compression: a curve costs rows where it bends, not one per step.

A training run writes its metrics far more often than anyone reads them back, and a viewer only ever draws
straight lines between the points it receives. Holding a point back is therefore free as long as the line
that will be drawn without it still passes within a tolerance of it. That tolerance is a fraction of the
curve's own amplitude, so a loss falling from 2.0 to 0.1 and an AUROC moving in the third decimal are both
thinned by the same rule.

This is the swinging door algorithm industrial historians have logged sensors with for decades.
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import math
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field

# Constants
METRIC_DEADBAND: float = 0.01
""" Fraction of a curve's own amplitude the drawn line may sit away from the curve it stands in for. """


# Classes
@dataclass
class MetricCurve:
	""" What one metric key has written so far, and the span of points it is holding back.

	The span is the range of slopes a line leaving :py:attr:`last_step` may still take while clearing every held point.
	It closes on the first point no such line reaches.
	"""
	last_step: int
	""" Step of the last point written, where the line currently being drawn starts. """
	last_val: float
	""" Value of that point. """
	low: float
	""" Smallest value seen, paired with :py:attr:`high` to scale the tolerance to the curve's own amplitude. """
	high: float
	""" Largest value seen. """
	pending: tuple[int, float] | None = None
	""" (step, value) last held back, written when the span closes and at flush() so a curve ends where the run did. """
	upper: float = math.inf
	""" Steepest slope the line may leave :py:attr:`last_step` on, above which a held point falls under it. """
	lower: float = -math.inf
	""" Shallowest slope it may leave on, below which a held point rises over it. """

	def admits(self, step: int, value: float) -> bool:
		""" Whether a straight line from the last written point to this one still clears every point held back.

		Reading the last two points instead asks a local question a smooth curve answers forever.
		A cosine sampled once per epoch is straight over one epoch, and would reach the UI as its two endpoints.

		>>> # A ramp holding steps 1 and 2, on a curve whose values span 0.0 to 2.0
		>>> curve = MetricCurve(last_step=0, last_val=0.0, low=0.0, high=2.0)
		>>> curve.hold(1, 1.0, deadband=0.01)
		>>> curve.hold(2, 2.0, deadband=0.01)
		>>> curve.admits(3, 3.0)
		True
		>>> curve.admits(3, 2.0)
		False
		"""
		return self.lower <= (value - self.last_val) / (step - self.last_step) <= self.upper

	def hold(self, step: int, value: float, deadband: float) -> None:
		""" Keep a point back, narrowing the slopes a line may still leave the last written point on.

		The tolerance is read off the amplitude seen so far, which only ever grows.
		A span opened early is judged against a narrower band than its last points would allow, so it writes a spare row.
		"""
		tolerance: float = deadband * (self.high - self.low)
		distance: int = step - self.last_step
		self.upper = min(self.upper, (value + tolerance - self.last_val) / distance)
		self.lower = max(self.lower, (value - tolerance - self.last_val) / distance)
		self.pending = (step, value)

	def anchor(self, step: int, value: float) -> None:
		""" Start the next line at a point that was just written, which is what stops the drawn one from drifting. """
		self.last_step, self.last_val = step, value
		self.upper, self.lower = math.inf, -math.inf
		self.pending = None


@dataclass
class DeadbandFilter:
	""" Thin a stream of metrics down to the corners of the line a viewer will draw through them.

	:py:meth:`feed` takes the points a step produced and hands back only those worth writing, keyed by the step
	each one belongs to. A point is usually held until a later one proves the line cannot reach it, so the step
	handed back is rarely the step just fed. :py:meth:`flush` releases what is still held, and every curve then
	ends where the run did.

	>>> deadband = DeadbandFilter()
	>>> deadband.feed({"loss": 1.0}, 0)
	{0: {'loss': 1.0}}
	>>> deadband.feed({"loss": 0.5}, 1)
	{}
	>>> deadband.feed({"loss": 0.0}, 2)
	{}
	>>> deadband.feed({"loss": 1.0}, 3)
	{2: {'loss': 0.0}}
	>>> deadband.flush()
	{3: {'loss': 1.0}}
	"""
	deadband: float = METRIC_DEADBAND
	""" Fraction of a curve's amplitude the drawn line may sit away from it, ``0.0`` writing every bend. """
	curves: dict[str, MetricCurve] = field(default_factory=dict[str, MetricCurve])
	""" What each key has written so far, and the span of points it is holding back. """

	def feed(self, metrics: Mapping[str, float], step: int = 0) -> dict[int, dict[str, float]]:
		""" Take one step's metrics and hand back what is now worth writing, grouped by the step it belongs to.

		Args:
			metrics: Values this step produced, one per key.
			step:    Step they were measured at, which has to grow for a key to ever write a second point.

		>>> deadband = DeadbandFilter()
		>>> deadband.feed({"a": 1.0, "b": 2.0})
		{0: {'a': 1.0, 'b': 2.0}}
		>>> deadband.feed({"a": 1.0}, 0)
		{}
		"""
		batched: defaultdict[int, dict[str, float]] = defaultdict(dict)
		for key, value in metrics.items():
			# A key writes its first point straight away, which is what gives the next ones a line to leave from
			curve: MetricCurve | None = self.curves.get(key)
			if curve is None:
				self.curves[key] = MetricCurve(last_step=step, last_val=value, low=value, high=value)
				batched[step][key] = value
				continue
			curve.low, curve.high = min(curve.low, value), max(curve.high, value)
			if step <= curve.last_step:
				continue

			held: tuple[int, float] | None = curve.pending
			if held is not None and not curve.admits(step, value):
				batched[held[0]][key] = held[1]
				curve.anchor(held[0], held[1])
			curve.hold(step, value, self.deadband)
		return dict(batched)

	def flush(self) -> dict[int, dict[str, float]]:
		""" Release the point every curve is holding, so each one ends where the run did.

		>>> DeadbandFilter().flush()
		{}
		"""
		batched: defaultdict[int, dict[str, float]] = defaultdict(dict)
		for key, curve in self.curves.items():
			if curve.pending is not None:
				step, value = curve.pending
				batched[step][key] = value
				curve.anchor(step, value)
		return dict(batched)

