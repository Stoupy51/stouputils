""" What LogToFile writes to its file, alone and combined with progress bars, child processes, nesting and Muffle. """
# Imports
import sys
import threading
from pathlib import Path

import stouputils as stp


# Functions
def read(path: Path) -> str:
	return path.read_text(encoding="utf-8")


def test_a_progress_bar_is_logged_once_in_its_final_state(tmp_path: Path) -> None:
	""" A bar redraws its line with carriage returns, which a file cannot undo, so only the last drawing belongs there. """
	with stp.LogToFile(str(tmp_path / "bar.log")):
		print("before")
		for _ in stp.progress_bar(range(20), desc="work"):
			pass
		print("after")
	lines: list[str] = read(tmp_path / "bar.log").splitlines()
	assert lines[0] == "before" and lines[-1] == "after"
	assert len(lines) == 3 and "work" in lines[1] and "20/20" in lines[1]


def test_windows_line_endings_survive(tmp_path: Path) -> None:
	with stp.LogToFile(str(tmp_path / "crlf.log")):
		sys.stdout.write("first\r\nsecond\r\n")
	assert read(tmp_path / "crlf.log").splitlines() == ["first", "second"]


def test_an_unfinished_last_line_is_still_written(tmp_path: Path) -> None:
	with stp.LogToFile(str(tmp_path / "partial.log")):
		print("no newline", end="")
	assert read(tmp_path / "partial.log") == "no newline"


def test_threads_writing_at_once_lose_no_line(tmp_path: Path) -> None:
	def write_lines(thread: int) -> None:
		for i in range(300):
			sys.stdout.write(f"{thread}-{i}\n")

	with stp.LogToFile(str(tmp_path / "threads.log")):
		threads: list[threading.Thread] = [threading.Thread(target=write_lines, args=(t,)) for t in range(8)]
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()
	assert sorted(read(tmp_path / "threads.log").splitlines()) == sorted(f"{t}-{i}" for t in range(8) for i in range(300))


def test_captured_child_processes_reach_the_file(tmp_path: Path) -> None:
	with stp.LogToFile(str(tmp_path / "children.log")):
		stp.run_in_subprocess(print, "from a subprocess")
		stp.multiprocessing(print, ["from worker 1", "from worker 2"], max_workers=2)
		stp.multiprocessing(print, ["from worker 3", "from worker 4"], max_workers=2, desc="pool")
	lines: list[str] = read(tmp_path / "children.log").splitlines()
	for expected in ("from a subprocess", "from worker 1", "from worker 2", "from worker 3", "from worker 4"):
		assert expected in lines
	assert any("pool" in line and "2/2" in line for line in lines)
	assert "" not in lines


def test_the_streams_are_restored_on_exit(tmp_path: Path) -> None:
	stdout, stderr = sys.stdout, sys.stderr
	with stp.LogToFile(str(tmp_path / "restore.log")):
		pass
	assert sys.stdout is stdout and sys.stderr is stderr


def test_a_nested_log_lands_in_both_files(tmp_path: Path) -> None:
	stdout = sys.stdout
	with stp.LogToFile(str(tmp_path / "outer.log")):
		print("outer 1")
		with stp.LogToFile(str(tmp_path / "inner.log")):
			print("inner")
		print("outer 2")
	assert read(tmp_path / "outer.log").splitlines() == ["outer 1", "inner", "outer 2"]
	assert read(tmp_path / "inner.log").splitlines() == ["inner"]
	assert sys.stdout is stdout


def test_changing_file_moves_the_log_and_still_restores(tmp_path: Path) -> None:
	stdout = sys.stdout
	with stp.LogToFile(str(tmp_path / "first.log")) as log:
		print("one")
		log.change_file(str(tmp_path / "second.log"))
		print("two")
	assert read(tmp_path / "first.log").splitlines() == ["one"]
	assert read(tmp_path / "second.log").splitlines() == ["two"]
	assert sys.stdout is stdout


def test_a_log_inside_a_muffle_is_written_and_unwinds(tmp_path: Path) -> None:
	stdout = sys.stdout
	with stp.Muffle(), stp.LogToFile(str(tmp_path / "muffled.log")):
		print("only in the file")
	assert read(tmp_path / "muffled.log").splitlines() == ["only in the file"]
	assert sys.stdout is stdout


def test_a_muffle_inside_a_log_keeps_its_silence_until_an_error(tmp_path: Path) -> None:
	with stp.LogToFile(str(tmp_path / "muffle_inside.log")):
		with stp.Muffle():
			print("muted")
		try:
			with stp.Muffle(replay_on_error=True):
				print("replayed")
				raise ValueError("boom")
		except ValueError:
			pass
	assert read(tmp_path / "muffle_inside.log").splitlines() == ["replayed"]

