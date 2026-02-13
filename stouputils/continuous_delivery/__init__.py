""" Continuous delivery and deployment utilities.

This module provides tools for automating software delivery and deployment:

Key Features:
- GitHub release management and uploads
- PyPI package publishing utilities
- pyproject.toml file management
- Common CD/CI utilities
- Local git changelog generation

Components:

- :py:mod:`~stouputils.continuous_delivery.cd_utils`: Common utilities for continuous delivery
- :py:mod:`~stouputils.continuous_delivery.git`: Local git changelog utilities (:py:func:`~stouputils.continuous_delivery.git.generate_local_changelog`, :py:func:`~stouputils.continuous_delivery.git.changelog_cli`)
- :py:mod:`~stouputils.continuous_delivery.github`: GitHub-specific utilities (:py:func:`~stouputils.continuous_delivery.github.upload_to_github`)
- :py:mod:`~stouputils.continuous_delivery.pypi`: PyPI publishing tools (:py:func:`~stouputils.continuous_delivery.pypi.pypi_full_routine`)
- :py:mod:`~stouputils.continuous_delivery.pyproject`: pyproject.toml file management
- :py:mod:`~stouputils.continuous_delivery.stubs`: Stub file generation using pyright (:py:func:`~stouputils.continuous_delivery.stubs.stubs_full_routine`)

"""  # noqa: E501
# Imports
from .cd_utils import *
from .git import *
from .github import *
from .pypi import *
from .pyproject import *
from .stubs import *

