""" What this process is actually allowed to use, as opposed to what the host reports.

The kernel interfaces every tool reads describe the machine, not the container. A pod capped at 12 of the
machine's 192 cores therefore reports 6 % CPU while it is saturated, and a 96 GiB cap against 2.4 TiB of host
RAM reads as 4 % while the pod is about to be killed. Cgroup v2 is where the real ceiling is stated.

- :py:func:`cpu_limit`
- :py:func:`memory_limit_megabytes`

Outside a capped container both fall back to the host, which is the right answer there.
Cgroup v1 is not read, its interface having been superseded on every distribution still receiving updates.

:py:attr:`~stouputils.config.StouputilsConfig.CPU_COUNT` and
:py:attr:`~stouputils.config.StouputilsConfig.MEMORY_MEGABYTES` are what the rest of the package reads these through.
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from .lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import os
from contextlib import suppress

# Constants
CPU_MAX_PATH: str = "/sys/fs/cgroup/cpu.max"
""" Cgroup v2 file holding ``"<quota> <period>"`` in microseconds, or ``"max <period>"`` when uncapped. """

MEMORY_MAX_PATH: str = "/sys/fs/cgroup/memory.max"
""" Cgroup v2 file holding the memory cap in bytes, or ``"max"`` when uncapped. """

MEMINFO_PATH: str = "/proc/meminfo"
""" Kernel file whose ``MemTotal`` line is the host fallback when no cgroup cap is set. """

MEGABYTE: int = 1024 ** 2
""" Bytes in the mebibyte memory limits are reported in. """


# Functions
def cpu_limit() -> float:
	""" Cores this process may use, falling back to the host's count outside a capped container.

	Fractional on purpose: a pod may be given half a core, and rounding that up or down is wrong either way.
	This is the ceiling itself, not a worker count. :py:attr:`StouputilsConfig.CPU_COUNT` is the latter,
	and it stays overridable by the usual thread-count environment variables.

	>>> cpu_limit() > 0
	True
	"""
	quota: float | None = parse_cpu_max(read_limit_file(CPU_MAX_PATH))
	return quota if quota is not None else float(os.cpu_count() or 1)


def memory_limit_megabytes() -> float:
	""" Mebibytes this process may use, falling back to the host's total outside a capped container.

	Returns ``0.0`` when neither is readable, which a caller reads as "unknown" rather than as "none left".

	>>> memory_limit_megabytes() >= 0
	True
	"""
	capped: float | None = parse_memory_max(read_limit_file(MEMORY_MAX_PATH))
	return capped if capped is not None else parse_meminfo_total(read_limit_file(MEMINFO_PATH))


def parse_cpu_max(raw: str) -> float | None:
	""" Cores a cgroup v2 ``cpu.max`` line allows, None when it sets no quota.

	Args:
		raw: Content of :py:data:`CPU_MAX_PATH`, empty when the file is absent.
	>>> parse_cpu_max("1200000 100000")
	12.0
	>>> parse_cpu_max("50000 100000")
	0.5
	>>> parse_cpu_max("max 100000") is None
	True
	>>> parse_cpu_max("") is None
	True
	"""
	quota, _, period = raw.strip().partition(" ")
	if not quota.isdigit() or not period.strip().isdigit() or int(period) == 0:
		return None
	return int(quota) / int(period)


def parse_memory_max(raw: str) -> float | None:
	""" Mebibytes a cgroup v2 ``memory.max`` line allows, None when it sets no cap.

	Args:
		raw: Content of :py:data:`MEMORY_MAX_PATH`, empty when the file is absent.
	>>> parse_memory_max("103079215104")
	98304.0
	>>> parse_memory_max("max") is None
	True
	"""
	stripped: str = raw.strip()
	return int(stripped) / MEGABYTE if stripped.isdigit() else None


def parse_meminfo_total(raw: str) -> float:
	""" Mebibytes the ``MemTotal`` line of ``/proc/meminfo`` reports, ``0.0`` when there is none.

	>>> parse_meminfo_total("MemTotal:       16302056 kB")
	15919.9765625
	>>> parse_meminfo_total("")
	0.0
	"""
	for line in raw.splitlines():
		if line.startswith("MemTotal:"):
			kilobytes: str = line.split()[1]
			return int(kilobytes) / 1024 if kilobytes.isdigit() else 0.0
	return 0.0


def read_limit_file(path: str) -> str:
	""" The file's content, empty when it does not exist or cannot be read.

	>>> read_limit_file("/nonexistent/cgroup/file")
	''
	"""
	with suppress(OSError), open(path, encoding="utf-8") as handle:
		return handle.read()
	return ""

