
# Imports
import os
import tempfile
import time
from multiprocessing import get_context
from typing import Any

from stouputils.lock import LockFifo, RLockFifo


def _safe_append(path: str, line: str) -> None:
	time.sleep(1) # Simulate some delay to increase chance of interleaving if locks fail
	with open(path, "a", encoding="utf-8") as f:
		f.write(line + "\n")
		f.flush()
		os.fsync(f.fileno())


# Worker for LockFifo: wait start_delay, acquire lock, write enter/leave with timestamps
def _lock_worker(lock_path: str, log_path: str, index: int, start_delay: float, cs_sleep: float) -> None:
	time.sleep(start_delay)
	start_attempt = time.time()
	_safe_append(log_path, f"attempt {index} {start_attempt} pid={os.getpid()}")
	with LockFifo(lock_path, timeout=10):
		enter = time.time()
		_safe_append(log_path, f"enter {index} {enter} pid={os.getpid()}")
		time.sleep(cs_sleep)
		leave = time.time()
		_safe_append(log_path, f"leave {index} {leave} pid={os.getpid()}")


# Worker for RLockFifo reentrancy test
def _rlock_worker(lock_path: str, log_path: str, index: int, start_delay: float, nested_sleep: float) -> None:
	time.sleep(start_delay)
	with RLockFifo(lock_path, timeout=10):
		_safe_append(log_path, f"enter_outer {index} {time.time()}")
		with RLockFifo(lock_path, timeout=10):
			_safe_append(log_path, f"enter_inner {index} {time.time()}")
			time.sleep(nested_sleep)
			_safe_append(log_path, f"leave_inner {index} {time.time()}")
		_safe_append(log_path, f"leave_outer {index} {time.time()}")


def test_lock_fifo_order(num_workers: int = 5, cs_sleep: float = 0.2) -> None:
	""" Spawn several processes that use LockFifo and ensure they enter critical section in FIFO order.

	This test starts workers with a small stagger so their "attempt" times define the expected order.
	We assert that "enter" records appear in the same order as worker indices, and each enter occurs
	after the previous worker's leave (within tolerance).
	"""
	with tempfile.TemporaryDirectory() as td:
		lock_path = os.path.join(td, "test.lock")
		log_path = os.path.join(td, "lock.log")

		# Ensure empty log
		open(log_path, "w").close()

		ctx = get_context("spawn")
		procs: list[Any] = []
		# start workers with a slightly larger stagger to reduce timing flakiness
		for i in range(num_workers):
			p = ctx.Process(target=_lock_worker, args=(lock_path, log_path, i, i * 0.1, cs_sleep))
			p.start()
			procs.append(p)

		for p in procs:
			p.join(timeout=10)
			assert not p.is_alive(), "Worker timed out"

		# Parse log
		lines = [line.strip() for line in open(log_path, encoding="utf-8").read().splitlines() if line.strip()]
		enter_records: list[tuple[int, float]] = []
		leave_records: list[tuple[int, float]] = []
		for line in lines:
			parts = line.split()
			if parts[0] == "enter":
				enter_records.append((int(parts[1]), float(parts[2])))
			elif parts[0] == "leave":
				leave_records.append((int(parts[1]), float(parts[2])))

		# Check enters order matches indices 0..n-1
		expected_indices = list(range(num_workers))
		observed_indices = [i for i, _ in enter_records]
		assert observed_indices == expected_indices, f"Enter order mismatch: expected {expected_indices} got {observed_indices}"

		# Ensure mutual exclusion: critical sections must not overlap. Build per-worker intervals
		enter_map = dict(enter_records)
		leave_map = dict(leave_records)
		for i in range(num_workers):
			if i not in enter_map or i not in leave_map:
				raise AssertionError(f"Missing enter/leave for worker {i}")
		# Check consecutive workers: previous leave should occur before current enter (allow tiny clock jitter)
		for i in range(1, num_workers):
			prev_leave = leave_map[i - 1]
			curr_enter = enter_map[i]
			# Allow tiny clock/timestamp discrepancies (1 ms)
			if curr_enter + 1e-3 < prev_leave:
				msg_lines = ["Lock ordering violation detected:"]
				msg_lines.append(f"Worker {i-1} leave: {prev_leave:.6f}")
				msg_lines.append(f"Worker {i} enter: {curr_enter:.6f}")
				msg_lines.append("Full log:")
				msg_lines.extend(lines)
				raise AssertionError("\n".join(msg_lines))

		print("test_lock_fifo_order: PASS")


def test_rlock_reentrancy_and_order() -> None:
	""" Test RLockFifo reentrancy (same process can re-acquire) and that other processes wait until full release. """
	with tempfile.TemporaryDirectory() as td:
		lock_path = os.path.join(td, "rlock.lock")
		log_path = os.path.join(td, "rlock.log")
		open(log_path, "w").close()

		ctx = get_context("spawn")
		p1 = ctx.Process(target=_rlock_worker, args=(lock_path, log_path, 0, 0.0, 0.25))
		p2 = ctx.Process(target=_rlock_worker, args=(lock_path, log_path, 1, 0.05, 0.01))
		p1.start()
		p2.start()
		p1.join(timeout=10)
		p2.join(timeout=10)
		assert not p1.is_alive() and not p2.is_alive(), "RLock workers timed out"

		lines = [line.strip() for line in open(log_path, encoding="utf-8").read().splitlines() if line.strip()]
		# We expect p1 enter_outer, enter_inner, leave_inner, leave_outer before any enter_outer from p2
		first_entries = lines[:4]
		expected_prefixes = ["enter_outer 0", "enter_inner 0", "leave_inner 0", "leave_outer 0"]
		for exp, got in zip(expected_prefixes, first_entries, strict=False):
			assert got.startswith(exp), f"Expected '{exp}' got '{got}'"

		print("test_rlock_reentrancy_and_order: PASS")


def main() -> None:
	print("Running lock tests...")
	test_lock_fifo_order()
	test_rlock_reentrancy_and_order()
	print("All lock tests passed")


if __name__ == "__main__":
	main()

