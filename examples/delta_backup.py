""" Backup CLI example and regression tests.

Examples:
	py examples/delta_backup.py delta "src" "backup" -x "*pycache*"
	py examples/delta_backup.py test
"""

# Imports
import hashlib
import sys
import tempfile
import zipfile
from collections.abc import Callable
from pathlib import Path

import stouputils.backup as app

DELETED_FILES_FILENAME: str = "__deleted_files__.txt"


def get_text_hash(content: str) -> str:
	""" Returns the SHA-256 hash for text content.

	Args:
		content (str): Text content to hash
	Returns:
		str: SHA-256 hash
	"""
	return hashlib.sha256(content.encode()).hexdigest()


def add_text_file_to_zip(zipf: zipfile.ZipFile, filename: str, content: str) -> None:
	""" Adds a text file with a valid backup hash comment to a ZIP file.

	Args:
		zipf (zipfile.ZipFile): ZIP file to write into
		filename (str): Archive filename
		content (str): File content
	"""
	zip_info: zipfile.ZipInfo = zipfile.ZipInfo(filename)
	zip_info.compress_type = zipfile.ZIP_DEFLATED
	zip_info.comment = get_text_hash(content).encode()
	zipf.writestr(zip_info, content)


def write_test_backup(backup_folder: Path, backup_name: str, files: dict[str, str], deleted_files: set[str] | None = None) -> Path:
	""" Writes a small delta backup ZIP for tests.

	Args:
		backup_folder (Path): Folder where the backup is written
		backup_name (str): Backup ZIP filename
		files (dict[str, str]): Mapping of archive filenames to text content
		deleted_files (set[str] | None): Deleted files to write as tombstones
	Returns:
		Path: Created ZIP path
	"""
	backup_path: Path = backup_folder / backup_name
	with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
		for filename, content in files.items():
			add_text_file_to_zip(zipf, filename, content)
		if deleted_files:
			zipf.writestr(DELETED_FILES_FILENAME, "\n".join(sorted(deleted_files)), compress_type=zipfile.ZIP_DEFLATED)
	return backup_path


def read_zip_text_files(zip_path: Path) -> dict[str, str]:
	""" Reads text files from a ZIP, excluding backup metadata.

	Args:
		zip_path (Path): ZIP file path
	Returns:
		dict[str, str]: Mapping of archive filenames to text content
	"""
	with zipfile.ZipFile(zip_path, "r") as zipf:
		return {
			filename: zipf.read(filename).decode()
			for filename in zipf.namelist()
			if filename != DELETED_FILES_FILENAME
		}


def read_deleted_files(zip_path: Path) -> set[str]:
	""" Reads deleted file tombstones from a ZIP.

	Args:
		zip_path (Path): ZIP file path
	Returns:
		set[str]: Deleted file names
	"""
	with zipfile.ZipFile(zip_path, "r") as zipf:
		if DELETED_FILES_FILENAME not in zipf.namelist():
			return set()
		return set(zipf.read(DELETED_FILES_FILENAME).decode().splitlines())


def get_zip_paths(folder: Path) -> list[Path]:
	""" Returns ZIP files in a folder sorted by filename.

	Args:
		folder (Path): Folder to inspect
	Returns:
		list[Path]: Sorted ZIP paths
	"""
	return sorted(folder.glob("*.zip"))


def assert_equal(actual: object, expected: object, message: str) -> None:
	""" Raises an assertion error when two values differ.

	Args:
		actual (object): Actual value
		expected (object): Expected value
		message (str): Assertion message
	"""
	if actual != expected:
		raise AssertionError(f"{message}\nExpected: {expected!r}\nActual: {actual!r}")


def test_newest_file_wins() -> None:
	""" Ensures consolidation keeps the newest version of a file."""
	with tempfile.TemporaryDirectory() as temp_dir:
		backup_folder: Path = Path(temp_dir)
		write_test_backup(backup_folder, "2026_05_18-04_00_47.zip", {"world/plot.txt": "old"})
		latest_backup: Path = write_test_backup(backup_folder, "2026_05_25-04_00_47.zip", {"world/plot.txt": "new"})
		destination_zip: Path = backup_folder / "out.zip"

		app.consolidate_backups(str(latest_backup), str(destination_zip))

		assert_equal(read_zip_text_files(destination_zip), {"world/plot.txt": "new"}, "Newest file content should override older content")


def test_deleted_file_is_not_restored() -> None:
	""" Ensures consolidation does not restore a file deleted by a newer backup."""
	with tempfile.TemporaryDirectory() as temp_dir:
		backup_folder: Path = Path(temp_dir)
		write_test_backup(backup_folder, "2026_05_18-04_00_47.zip", {"world/plot.txt": "old", "world/keep.txt": "keep"})
		latest_backup: Path = write_test_backup(backup_folder, "2026_05_25-04_00_47.zip", {}, {"world/plot.txt"})
		destination_zip: Path = backup_folder / "out.zip"

		app.consolidate_backups(str(latest_backup), str(destination_zip))

		assert_equal(read_zip_text_files(destination_zip), {"world/keep.txt": "keep"}, "Deleted files should not be restored from older backups")
		assert_equal(read_deleted_files(destination_zip), {"world/plot.txt"}, "The consolidated backup should keep active tombstones")


def test_recreated_file_wins_over_older_tombstone() -> None:
	""" Ensures a recreated file is kept even when an older backup contains its tombstone."""
	with tempfile.TemporaryDirectory() as temp_dir:
		backup_folder: Path = Path(temp_dir)
		write_test_backup(backup_folder, "2026_05_18-04_00_47.zip", {"world/plot.txt": "old"})
		write_test_backup(backup_folder, "2026_05_25-04_00_47.zip", {}, {"world/plot.txt"})
		latest_backup: Path = write_test_backup(backup_folder, "2026_06_01-04_00_49.zip", {"world/plot.txt": "new"})
		destination_zip: Path = backup_folder / "out.zip"

		app.consolidate_backups(str(latest_backup), str(destination_zip))

		assert_equal(read_zip_text_files(destination_zip), {"world/plot.txt": "new"}, "Recreated files should beat older deletion tombstones")
		assert_equal(read_deleted_files(destination_zip), set[str](), "Resolved tombstones should not be copied into the consolidated backup")


def test_consolidated_backup_is_sorted_chronologically() -> None:
	""" Ensures consolidated backups are included according to their timestamp."""
	with tempfile.TemporaryDirectory() as temp_dir:
		backup_folder: Path = Path(temp_dir)
		consolidated_backup: Path = write_test_backup(backup_folder, "consolidated_2026_05_15-20_34_23.zip", {"world/base.txt": "base"})
		write_test_backup(backup_folder, "2026_05_18-04_00_47.zip", {"world/plot.txt": "old"})
		write_test_backup(backup_folder, "2026_05_25-04_00_47.zip", {"world/plot.txt": "middle"})
		latest_backup: Path = write_test_backup(backup_folder, "2026_06_01-04_00_49.zip", {"world/plot.txt": "new"})
		destination_zip: Path = backup_folder / "out.zip"

		previous_backups: dict[str, dict[str, str]] = app.get_all_previous_backups(str(backup_folder), all_before=str(latest_backup))
		previous_backup_names: list[str] = [Path(backup_path).name for backup_path in previous_backups]

		app.consolidate_backups(str(latest_backup), str(destination_zip))

		assert_equal(previous_backup_names[-1], consolidated_backup.name, "Consolidated backups should be sorted by their embedded timestamp")
		assert_equal(read_zip_text_files(destination_zip), {"world/base.txt": "base", "world/plot.txt": "new"}, "Consolidation should include older consolidated backups")


def test_delta_backup_detects_revert_to_old_content() -> None:
	""" Ensures a file reverted to an older hash is backed up as a new change."""
	with tempfile.TemporaryDirectory() as temp_dir:
		root: Path = Path(temp_dir)
		source_folder: Path = root / "source"
		backup_root: Path = root / "backups"
		source_backup_folder: Path = backup_root / source_folder.name
		source_folder.mkdir()
		source_backup_folder.mkdir(parents=True)
		(source_folder / "plot.txt").write_text("old", encoding="utf-8")
		write_test_backup(source_backup_folder, "2026_05_18-04_00_47.zip", {"source/plot.txt": "old"})
		write_test_backup(source_backup_folder, "2026_05_25-04_00_47.zip", {"source/plot.txt": "new"})

		app.create_delta_backup(str(source_folder), str(backup_root))

		created_backups: list[Path] = [zip_path for zip_path in get_zip_paths(source_backup_folder) if zip_path.name not in {"2026_05_18-04_00_47.zip", "2026_05_25-04_00_47.zip"}]
		assert_equal(len(created_backups), 1, "Reverting to an older hash should create a new delta backup")
		assert_equal(read_zip_text_files(created_backups[0]), {"source/plot.txt": "old"}, "The reverted file should be stored in the new delta backup")


def test_delta_backup_detects_same_content_recreation_after_delete() -> None:
	""" Ensures recreating a deleted file with the same old content is backed up."""
	with tempfile.TemporaryDirectory() as temp_dir:
		root: Path = Path(temp_dir)
		source_folder: Path = root / "source"
		backup_root: Path = root / "backups"
		source_backup_folder: Path = backup_root / source_folder.name
		source_folder.mkdir()
		source_backup_folder.mkdir(parents=True)
		(source_folder / "plot.txt").write_text("old", encoding="utf-8")
		write_test_backup(source_backup_folder, "2026_05_18-04_00_47.zip", {"source/plot.txt": "old"})
		write_test_backup(source_backup_folder, "2026_05_25-04_00_47.zip", {}, {"source/plot.txt"})

		app.create_delta_backup(str(source_folder), str(backup_root))

		created_backups: list[Path] = [zip_path for zip_path in get_zip_paths(source_backup_folder) if zip_path.name not in {"2026_05_18-04_00_47.zip", "2026_05_25-04_00_47.zip"}]
		assert_equal(len(created_backups), 1, "Recreating a deleted file with the same content should create a new delta backup")
		assert_equal(read_zip_text_files(created_backups[0]), {"source/plot.txt": "old"}, "The recreated file should be stored in the new delta backup")


def run_backup_tests() -> None:
	""" Runs all backup regression tests."""
	tests: list[tuple[str, Callable[[], None]]] = [
		("newest file wins", test_newest_file_wins),
		("deleted file is not restored", test_deleted_file_is_not_restored),
		("recreated file wins over older tombstone", test_recreated_file_wins_over_older_tombstone),
		("consolidated backup is sorted chronologically", test_consolidated_backup_is_sorted_chronologically),
		("delta backup detects revert to old content", test_delta_backup_detects_revert_to_old_content),
		("delta backup detects same content recreation after delete", test_delta_backup_detects_same_content_recreation_after_delete),
	]

	for test_name, test_func in tests:
		test_func()
		print(f"OK - {test_name}")


if __name__ == "__main__":
	if len(sys.argv) > 1 and sys.argv[1] == "test":
		run_backup_tests()
	else:
		app.backup_cli()

