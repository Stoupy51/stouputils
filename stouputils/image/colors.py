""" Colour maths for deciding what to draw on top of a filled shape.

Charts, heatmaps and legends all face the same question: black text or white text on this patch?
Answering it from the sRGB luminance keeps every annotation readable, whatever colormap produced the patch.
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from collections.abc import Iterable


# Functions
def relative_luminance(color: Iterable[float]) -> float:
	""" Perceived brightness of a colour, as the sRGB relative luminance (https://en.wikipedia.org/wiki/Relative_luminance).

	Channels are linearised before being weighted, since sRGB stores them gamma-encoded.
	Averaging the raw channels instead would rate a saturated blue as bright as a saturated green.

	Args:
		color (Iterable[float]): RGB or RGBA channels in ``[0.0, 1.0]``; anything past the third is ignored.
	Returns:
		float: Luminance in ``[0.0, 1.0]``, ``0.0`` being black and ``1.0`` white.

	Examples:
		>>> relative_luminance((0.0, 0.0, 0.0))
		0.0
		>>> relative_luminance((1.0, 1.0, 1.0, 1.0))
		1.0
		>>> round(relative_luminance((1.0, 0.0, 0.0)), 4)
		0.2126
		>>> round(relative_luminance((0.0, 0.0, 1.0)), 4)
		0.0722
	"""
	red, green, blue = (
		channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
		for channel in tuple(color)[:3]
	)
	return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def readable_text_color(
	color: Iterable[float],
	on_light: str = "black",
	on_dark: str = "white",
	threshold: float = 0.4,
) -> str:
	""" Pick the text colour that stays readable on top of a given background colour.

	Args:
		color     (Iterable[float]): Background RGB or RGBA channels in ``[0.0, 1.0]``.
		on_light  (str):             Returned when the background is light, ex: "black" or "#222222".
		on_dark   (str):             Returned when the background is dark.
		threshold (float):           Luminance above which the background counts as light.
	Returns:
		str: Either ``on_light`` or ``on_dark``, untouched, so any colour syntax the caller uses goes through.

	Examples:
		>>> readable_text_color((1.0, 1.0, 1.0))
		'black'
		>>> readable_text_color((0.27, 0.0, 0.33, 1.0))
		'white'
		>>> readable_text_color((0.99, 0.91, 0.14), on_light=".1")
		'.1'
	"""
	return on_light if relative_luminance(color) > threshold else on_dark

