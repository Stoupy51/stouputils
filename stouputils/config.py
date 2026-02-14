""" Global configuration module for stouputils.

This module provides the StouputilsConfig class which contains global configuration options
that control the behavior of various stouputils functions. Configuration values can be set
programmatically or via environment variables.

Environment Variables:
	Configuration options can be overridden using environment variables with the prefix
	``STP_`` or ``STOUPUTILS_`` followed by the configuration variable name.

	Examples:
		STP_PROCESS_TITLE_PER_WORKER=false
		STOUPUTILS_PROCESS_TITLE_PER_WORKER=true

Usage:
	.. code-block:: python

		from stouputils.config import StouputilsConfig as Cfg

		# Change configuration programmatically
		Cfg.PROCESS_TITLE_PER_WORKER = False
"""

# Imports
import os
from typing import Any, ClassVar


class StouputilsConfig:
	""" Global configuration class for stouputils. """

	VERBOSE_READING_ENV: bool = False
	""" Configuration option for verbose output when reading environment variables when stouputils is imported.\n
	- If true, stouputils will print out the environment variables it reads and their values. Defaults to False. """

	# Colors & formatting (used by `print` module)
	RESET: str = "\033[0m"
	RED: str = "\033[91m"
	GREEN: str = "\033[92m"
	YELLOW: str = "\033[93m"
	BLUE: str = "\033[94m"
	MAGENTA: str = "\033[95m"
	CYAN: str = "\033[96m"
	LINE_UP: str = "\033[1A"
	BOLD: str = "\033[1m"
	""" Terminal color/style constants used throughout the package.

	Used by: :mod:`stouputils.print` and other modules that output colored text (e.g., :mod:`stouputils.backup`, :mod:`stouputils.version_pkg`, ...). """

	BAR_FORMAT: str = "{l_bar}{bar}" + MAGENTA + "| {n_fmt}/{total_fmt} [{rate_fmt}{postfix}, {elapsed}<{remaining}]" + RESET
	""" Default bar format used for TQDM progress bars.

	Used by: :mod:`stouputils.print` and :mod:`stouputils.parallel` for progress bars. """

	# Modify logging level for all handle_error decorators
	FORCE_RAISE_EXCEPTION: bool = False
	""" If true, error_log parameter will be set to :attr:`LogLevels.RAISE_EXCEPTION` for every next handle_error calls,
	useful for :mod:`stouputils.all_doctests` to ensure exceptions are raised during testing instead of just logged. """

	# Parallel / process settings
	CPU_COUNT: int = os.cpu_count() or 1
	""" Number of CPUs to use by default for parallel operations (int).

	Used by: :mod:`stouputils.parallel` (modules ``common`` and ``multi``) and other concurrency helpers. """

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

	# GitHub defaults
	GITHUB_API_URL: str = "https://api.github.com"
	"""Base GitHub API URL used by the continuous_delivery utilities.

	Used by: :mod:`stouputils.continuous_delivery.github` for API endpoints. """

	# Conventional commit mapping used by continuous delivery changelog utilities
	COMMIT_TYPES: ClassVar[dict[str, str]] = {
		"feat":		"Features",
		"fix":		"Bug Fixes",
		"docs":		"Documentation",
		"style":	"Style",
		"chore":	"Chores",
		"refactor":	"Code Refactoring",
		"perf":		"Performance Improvements",
		"test":		"Tests",
		"build":	"Build System",
		"ci":		"CI/CD",
		"wip":		"Work in Progress",
		"revert":	"Reverts",
		"uwu":		"UwU ༼ つ ◕_◕ ༽つ",
	}
	""" Mapping of conventional commit short types to human-friendly headings used in changelogs.

	Used by: :mod:`stouputils.continuous_delivery.cd_utils` (parsing and grouping conventional commits for changelogs). """

	# Automatic docs requirements (kept here to avoid generic name conflicts)
	AUTO_DOCS_REQUIREMENTS: tuple[str, ...] = ("myst_parser",)
	""" List of requirements used by the automatic docs utilities.

	Used by: :mod:`stouputils.applications.automatic_docs` (dependency checks for documentation generation). """








# Change the default configuration depending on environment variables
def handle_config_from_env(var: str, expected_type: str) -> None:

	# Get environment variable
	env_name: str = f"STP_{var}"
	env_name_alt: str = f"STOUPUTILS_{var}"
	env_1: str | None = os.getenv(env_name)
	env_2: str | None = os.getenv(env_name_alt)
	env: str | None = env_1 or env_2
	if env_2:
		env_name = env_name_alt

	# Handle value
	if env is not None:
		if StouputilsConfig.VERBOSE_READING_ENV:
			print(f"Reading environment variable '{env_name}': {env}")

		value: Any
		if expected_type == "bool":
			value = env.lower() in ("true", "1", "yes")
		elif expected_type == "int":
			try:
				value = int(env)
			except ValueError as e:
				raise ValueError(f"Invalid integer value for environment variable '{env_name}': {env}") from e
		elif expected_type == "float":
			try:
				value = float(env)
			except ValueError as e:
				raise ValueError(f"Invalid float value for environment variable '{env_name}': {env}") from e
		else:
			value = env
		setattr(StouputilsConfig, var, value)

# Handle all configuration options from environment variables
for var, annotated_type in StouputilsConfig.__annotations__.items():
	type_str: str = annotated_type.__name__
	handle_config_from_env(var, type_str)

