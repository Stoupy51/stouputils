""" ⚙️ Global configuration module for stouputils.

This module provides the StouputilsConfig class which contains global configuration options
that control the behavior of various stouputils functions. Configuration values can be set
programmatically or via environment variables.

Environment Variables:
	Configuration options can be overridden using environment variables with the prefix
	``STP_`` or ``STOUPUTILS_`` followed by the configuration variable name.
	STP_PROCESS_TITLE_PER_WORKER=false
	STOUPUTILS_PROCESS_TITLE_PER_WORKER=true

Usage:
	.. code-block:: python

		from stouputils.config import StouputilsConfig as Cfg

		# Change configuration programmatically
		Cfg.PROCESS_TITLE_PER_WORKER = False
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from .lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import os
from collections.abc import Callable
from typing import Any, ClassVar

from .system import cpu_limit, memory_limit_megabytes

# Constants
ENV_PARSERS: dict[str, Callable[[str], Any]] = {
	"bool": lambda env: env.lower() in ("true", "1", "yes"),
	"int": int,
	"float": float,
}
""" How an environment variable is read, by the type name of the option it overrides. Any other type keeps the string. """


# Classes
class StouputilsConfig:
	""" Global configuration class for stouputils. """

	VERBOSE_READING_ENV: bool = False
	""" Configuration option for verbose output when reading environment variables when stouputils is imported.\n
	- If true, stouputils will print out the environment variables it reads and their values. Defaults to False. """

	# Colors & formatting (used by `print` module)
	RESET: str = "\x1b[0m"
	BLACK: str = "\x1b[30m"
	LIGHT_GRAY: str = "\x1b[37m"
	GRAY: str = "\x1b[90m"
	RED: str = "\x1b[91m"
	GREEN: str = "\x1b[92m"
	YELLOW: str = "\x1b[93m"
	BLUE: str = "\x1b[94m"
	MAGENTA: str = "\x1b[95m"
	CYAN: str = "\x1b[96m"
	WHITE: str = "\x1b[97m"
	LINE_UP: str = "\x1b[1A"
	BOLD: str = "\x1b[1m"
	""" Terminal color/style constants used throughout the package.

	Used by :mod:`stouputils.print` and the other modules printing colored text, such as :mod:`stouputils.backup`. """

	BAR_FORMAT: str = "{l_bar}{bar}" + MAGENTA + "| {n_fmt}/{total_fmt} [{rate_fmt}{postfix}, {elapsed}<{remaining}]" + RESET
	""" Default bar format used for TQDM progress bars.

	Used by: :mod:`stouputils.print` and :mod:`stouputils.parallel` for progress bars. """

	# Modify logging level for all handle_error decorators
	FORCE_RAISE_EXCEPTION: bool = False
	""" If true, error_log parameter will be set to :attr:`LogLevels.RAISE_EXCEPTION` for every next handle_error calls,
	useful for :mod:`stouputils.all_doctests` to ensure exceptions are raised during testing instead of just logged. """

	# Parallel / process settings
	CPU_COUNT: int = max(1, int(os.environ.get("OMP_NUM_THREADS", os.environ.get("MKL_NUM_THREADS", int(cpu_limit())))))
	""" Number of CPUs to use by default for parallel operations (int).
	Can be overridden by setting the OMP_NUM_THREADS or MKL_NUM_THREADS environment variables.

	Used by: :mod:`stouputils.parallel` (modules ``common`` and ``multi``) and other concurrency helpers. """

	MEMORY_MEGABYTES: float = memory_limit_megabytes()
	""" Memory this process may use, in MB, which is the container's cap wherever it states one.
	``0.0`` means neither the cap nor the host total could be read.

	Used by: :mod:`stouputils.mlflow` (denominator of ``process/memory_usage_percentage``). """

	PROCESS_TITLE_PER_WORKER: bool = True
	""" Configuration option for process title in multiprocessing() function.
	- If true, process title is set only once per worker (reflecting worker index 0 to max_workers-1).
	- If false, process title is updated for each task (reflecting task index 0 to len(args)-1).

	Defaults to True for easier/accurate worker identification.

	Used by: :mod:`stouputils.parallel.multi` (see :py:func:`~stouputils.parallel.multi.process_title_wrapper`). """

	# I/O buffer sizes
	CHUNK_SIZE: int = 1024 * 1024  # 1MB chunks for I/O operations
	""" Default chunk size for file I/O operations (bytes).

	Used by: :mod:`stouputils.backup` and other modules performing chunked file operations. """

	LARGE_CHUNK_SIZE: int = 8 * 1024 * 1024  # 8MB chunks for large file operations
	""" Larger chunk size for file I/O operations (bytes).

	Used by: :mod:`stouputils.backup` and other modules needing larger I/O buffers. """

	# Conventional commit mapping used by continuous delivery changelog utilities
	COMMIT_TYPES: ClassVar[dict[str, str]] = {
		"feat":     "Features",
		"fix":      "Bug Fixes",
		"docs":     "Documentation",
		"style":    "Style",
		"chore":    "Chores",
		"refactor": "Code Refactoring",
		"perf":     "Performance Improvements",
		"test":     "Tests",
		"build":    "Build System",
		"release":  "Releases",
		"api":      "API Changes",
		"ci":       "Continuous Integration",
		"cd":       "Continuous Delivery",
		"ci/cd":    "CI/CD",
		"security": "Security",
		"deps":     "Dependency Updates",
		"dep":      "Dependency Updates",
		"wip":      "Work in Progress",
		"hack":     "Don't ask",
		"revert":   "Reverts",
		"init":     "Initial Commit",
		"uwu":      "UwU ༼ つ ◕_◕ ༽つ",
	}
	""" Mapping of conventional commit short types to human-friendly headings used in changelogs.

	Used by: :mod:`stouputils.continuous_delivery.cd_utils` (parsing and grouping conventional commits for changelogs). """

	# Automatic docs requirements (kept here to avoid generic name conflicts)
	AUTO_DOCS_REQUIREMENTS: tuple[str, ...] = ("myst_parser",)
	""" List of requirements used by the automatic docs utilities.

	Used by: :mod:`stouputils.applications.automatic_docs` (dependency checks for documentation generation). """

	# Color cycle for numpy_segments_to_obj
	SEGMENTS_UNIQUE_COLOR: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 1.0)
	""" Color :func:`~stouputils.image.segments_export.add_default_colors_to_segments` gives the first segment unless skipped. """
	SEGMENTS_COLOR_CYCLE: tuple[tuple[float, float, float, float], ...] = (
		(0.0, 1.0, 0.0, 1.0),  # Green
		(0.0, 0.0, 1.0, 1.0),  # Blue
		(1.0, 1.0, 0.0, 1.0),  # Yellow
		(1.0, 0.0, 1.0, 1.0),  # Magenta
		(0.0, 1.0, 1.0, 1.0),  # Cyan
	)
	""" Colors :func:`~stouputils.image.segments_export.add_default_colors_to_segments` cycles through for the other segments. """






# Change the default configuration depending on environment variables
def handle_config_from_env(var: str, expected_type: str) -> None:
	env_name: str = f"STP_{var}" if os.getenv(f"STP_{var}") else f"STOUPUTILS_{var}"
	env: str | None = os.getenv(env_name)
	if env is None:
		return

	if StouputilsConfig.VERBOSE_READING_ENV:
		print(f"Reading environment variable '{env_name}': {env}")
	try:
		setattr(StouputilsConfig, var, ENV_PARSERS.get(expected_type, str)(env))
	except ValueError as e:
		raise ValueError(f"Invalid {expected_type} value for environment variable '{env_name}': {env}") from e

# Handle all configuration options from environment variables
for var, annotated_type in StouputilsConfig.__annotations__.items():
	type_str: str = annotated_type.__name__
	handle_config_from_env(var, type_str)

