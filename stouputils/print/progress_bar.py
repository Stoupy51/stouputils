
# Imports
from collections.abc import Iterable, Iterator
from typing import Any

from ..config import StouputilsConfig as Cfg


# Colored for loop function
def colored_for_loop[T](
	iterable: Iterable[T],
	desc: str = "Processing",
	color: str = Cfg.MAGENTA,
	bar_format: str = Cfg.BAR_FORMAT,
	ascii: bool = False,
	smooth_tqdm: bool = True,
	**kwargs: Any
) -> Iterator[T]:
	""" Function to iterate over a list with a colored TQDM progress bar like the other functions in this module.

	Args:
		iterable	(Iterable):			List to iterate over
		desc		(str):				Description of the function execution displayed in the progress bar
		color		(str):				Color of the progress bar (Defaults to ::attr::MAGENTA)
		bar_format	(str):				Format of the progress bar (Defaults to ::attr::BAR_FORMAT)
		ascii		(bool):				Whether to use ASCII or Unicode characters for the progress bar (Defaults to False)
		smooth_tqdm	(bool):				Whether to enable smooth progress bar updates by setting miniters=1 and mininterval=0.0 (Defaults to True)
		**kwargs:						Additional arguments to pass to the TQDM progress bar

	Yields:
		T: Each item of the iterable

	Examples:
		>>> import time
		>>> for i in colored_for_loop(range(10), desc="Time sleeping loop"):
		...     time.sleep(0.01)  # doctest: +SKIP
		>>> # Time sleeping loop: 100%|██████████████████| 10/10 [ 95.72it/s, 00:00<00:00]
	"""
	if bar_format == Cfg.BAR_FORMAT:
		bar_format = bar_format.replace(Cfg.MAGENTA, color)
	desc = color + desc

	if smooth_tqdm:
		kwargs.setdefault("mininterval", 0.0)
		try:
			total = len(iterable) # type: ignore
			import shutil
			width = shutil.get_terminal_size().columns
			kwargs.setdefault("miniters", max(1, total // width))
		except (TypeError, OSError):
			kwargs.setdefault("miniters", 1)

	from tqdm.auto import tqdm
	yield from tqdm(iterable, desc=desc, bar_format=bar_format, ascii=ascii, **kwargs)


