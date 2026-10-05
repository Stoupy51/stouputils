""" What LogToFile writes to its file, alone and combined with progress bars, threads, child processes, nesting and Muffle. """
# Imports
import importlib
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

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


def test_an_unfinished_line_reaches_the_file_right_away(tmp_path: Path) -> None:
	""" A long step announced without a newline must show in a tailed log before the step ends. """
	with stp.LogToFile(str(tmp_path / "partial.log")) as log:
		print("Processing...", end="", flush=True)
		log.file.flush()
		assert read(tmp_path / "partial.log") == "Processing..."
		print(" done")
	assert read(tmp_path / "partial.log") == "Processing... done\n"


def test_a_repeated_message_is_logged_first_and_last(tmp_path: Path) -> None:
	""" The terminal folds repeats into one counted line, the file keeps when the series started and how long it ran. """
	with stp.LogToFile(str(tmp_path / "repeat.log")):
		for _ in range(500):
			stp.info("same message")
		stp.info("other message")
	lines: list[str] = read(tmp_path / "repeat.log").splitlines()
	assert len(lines) == 3
	assert "same message" in lines[0] and "(x" not in lines[0]
	assert "(x500) same message" in lines[1]
	assert "other message" in lines[2]


def test_a_long_redrawn_line_leaves_checkpoints() -> None:
	""" A run killed during a progress bar must leave in the log how far the bar went. """
	state = stp.LineState(checkpoint_seconds=0.05)
	written: str = state.feed("\r 10%")
	time.sleep(0.06)
	written += state.feed("\r 50%") + state.feed("\r 60%")
	assert written == " 50%\n"
	assert state.feed("\r100%\n") == "100%\n"


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


def test_threads_logging_on_their_own_keep_their_files_apart(tmp_path: Path) -> None:
	stdout = sys.stdout

	def task(index: int) -> None:
		with stp.LogToFile(str(tmp_path / f"task_{index}.log")):
			for step in range(3):
				print(f"task {index} step {step}")
				time.sleep(0.005 * (index + 1))

	with stp.LogToFile(str(tmp_path / "parent.log")):
		stp.multithreading(task, range(3), max_workers=3)
		print("parent end")
	for index in range(3):
		assert read(tmp_path / f"task_{index}.log").splitlines() == [f"task {index} step {step}" for step in range(3)]
	expected: list[str] = [f"task {i} step {s}" for i in range(3) for s in range(3)] + ["parent end"]
	assert sorted(read(tmp_path / "parent.log").splitlines()) == sorted(expected)
	assert sys.stdout is stdout


def test_threads_logging_without_a_parent_log_still_unwind(tmp_path: Path) -> None:
	stdout = sys.stdout

	def task(index: int) -> None:
		with stp.LogToFile(str(tmp_path / f"alone_{index}.log")):
			time.sleep(0.01 * (3 - index))
			print(f"alone {index}")

	stp.multithreading(task, range(3), max_workers=3)
	for index in range(3):
		assert read(tmp_path / f"alone_{index}.log").splitlines() == [f"alone {index}"]
	assert sys.stdout is stdout


def test_processes_logging_on_their_own_keep_their_files_apart(tmp_path: Path) -> None:
	""" Each worker is a process of its own, with its own streams, while the parent log still gets their output. """
	(tmp_path / "logged_jobs.py").write_text(
		"import stouputils as stp\n"
		"def task(args):\n"
		"\tfolder, index = args\n"
		"\twith stp.LogToFile(f'{folder}/process_{index}.log'):\n"
		"\t\tprint(f'process {index}')\n"
	)
	sys.path.insert(0, str(tmp_path))
	try:
		jobs = importlib.import_module("logged_jobs")
		with stp.LogToFile(str(tmp_path / "parent.log")):
			stp.multiprocessing(jobs.task, [(str(tmp_path), i) for i in range(3)], max_workers=3)
	finally:
		sys.path.remove(str(tmp_path))
	for index in range(3):
		assert read(tmp_path / f"process_{index}.log").splitlines() == [f"process {index}"]
	assert sorted(read(tmp_path / "parent.log").splitlines()) == [f"process {i}" for i in range(3)]


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


def test_a_log_inside_a_muffle_inside_a_log_only_gets_its_own_lines(tmp_path: Path) -> None:
	stdout = sys.stdout
	with stp.LogToFile(str(tmp_path / "outer.log")):
		print("outer")
		with stp.Muffle(), stp.LogToFile(str(tmp_path / "inner.log")):
			print("inner")
		print("outer again")
	assert read(tmp_path / "outer.log").splitlines() == ["outer", "outer again"]
	assert read(tmp_path / "inner.log").splitlines() == ["inner"]
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


def run_script(tmp_path: Path, code: str) -> subprocess.CompletedProcess[str]:
	""" Run a Python script in a process of its own, so its descriptors are its own and not pytest's capture. """
	(tmp_path / "script.py").write_text(code)
	return subprocess.run([sys.executable, str(tmp_path / "script.py")], capture_output=True, text=True, cwd=tmp_path, timeout=120)


def test_capturing_descriptors_logs_what_bypasses_python(tmp_path: Path) -> None:
	""" Shell commands and children that do not capture their output only reach the descriptors. """
	result = run_script(tmp_path, (
		"import os, subprocess, sys\n"
		"import stouputils as stp\n"
		"if __name__ == '__main__':\n"
		"\twith stp.LogToFile('captured.log', capture_fd=True):\n"
		"\t\tprint('python line', flush=True)\n"
		"\t\tos.system('echo shell line')\n"
		"\t\tsubprocess.run([sys.executable, '-c', 'print(\"child line\")'])\n"
		"\t\tprint('python end')\n"
		"\tprint('after the block')\n"
	))
	assert result.returncode == 0, result.stderr
	assert result.stdout.splitlines() == ["python line", "shell line", "child line", "python end", "after the block"]
	logged: list[str] = read(tmp_path / "captured.log").splitlines()
	if os.name == "nt":
		assert logged == ["python line", "python end"] and "cannot capture" in result.stdout + result.stderr
	else:
		assert logged == ["python line", "shell line", "child line", "python end"]


def test_capturing_descriptors_is_skipped_outside_the_main_thread(tmp_path: Path) -> None:
	stdout = sys.stdout

	def task(_: int) -> None:
		with stp.LogToFile(str(tmp_path / "thread.log"), capture_fd=True):
			print("from a thread")

	stp.multithreading(task, [0, 1], max_workers=1)
	assert read(tmp_path / "thread.log").splitlines() == ["from a thread"]
	assert sys.stdout is stdout


def test_capturing_descriptors_in_jupyter_falls_back_to_python_output(tmp_path: Path) -> None:
	""" A notebook's stdout is not descriptor 1, so the log falls back to what Python writes. """
	nbformat: Any = pytest.importorskip("nbformat")
	nbclient: Any = pytest.importorskip("nbclient")
	pytest.importorskip("ipykernel")
	notebook = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(
		"import stouputils as stp\n"
		f"with stp.LogToFile({str(tmp_path / 'notebook.log')!r}, capture_fd=True):\n"
		"    print('from the notebook')\n"
	)])
	nbclient.NotebookClient(notebook, timeout=120, kernel_name="python3").execute()
	outputs: str = str(notebook.cells[0].outputs)
	assert "from the notebook" in outputs and "cannot capture" in outputs
	assert read(tmp_path / "notebook.log").splitlines() == ["from the notebook"]

