""" Installer module for stouputils.

Provides functions for platform-agnostic installation tasks by dispatching
to platform-specific implementations (Windows, Linux/macOS).

It handles getting installation paths, adding programs to the PATH environment variable,
and installing programs from local zip files or URLs.
"""
# ruff: noqa: F403
# ruff: noqa: F405

# Imports
from .common import *
from .downloader import *
from .linux import *
from .main import *
from .windows import *

