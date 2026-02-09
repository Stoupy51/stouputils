""" Global configuration module for stouputils.

This module provides the StouputilsConfig class which contains global configuration options
that control the behavior of various stouputils functions. Configuration values can be set
programmatically or via environment variables.

Environment Variables:
	Configuration options can be overridden using environment variables with the prefix
	STP_ or STOUPUTILS_ followed by the configuration variable name.

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
from typing import Any


class StouputilsConfig:

	VERBOSE_READING_ENV: bool = False
	""" Configuration option for verbose output when reading environment variables when stouputils is imported.
	If true, stouputils will print out the environment variables it reads and their values. Defaults to False. """

	PROCESS_TITLE_PER_WORKER: bool = True
	""" Configuration option for process title in multiprocessing() function.
	If true, process title is set only once per worker (reflecting worker index 0 to max_workers-1).
	If false, process title is updated for each task (reflecting task index 0 to len(args)-1).
	Defaults to True for easier/accurate worker identification. """








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

