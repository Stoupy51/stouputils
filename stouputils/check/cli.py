""" Command line of ``stouputils check``: which files to read, the rules on any text file, and the report. """

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import argparse
import re
import subprocess
import sys
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import fields, replace
from pathlib import Path

from ..config import StouputilsConfig as Cfg
from .python import python_errors, suppressions
from .rules import RULES, CheckConfig, Suppression, Violation

# Constants
BANNED_CHARACTERS: re.Pattern[str] = re.compile(
	r"[\N{EM DASH}\N{EN DASH}\N{HORIZONTAL ELLIPSIS}\N{MULTIPLICATION SIGN}\N{RIGHTWARDS ARROW}"
	r"\N{LEFT SINGLE QUOTATION MARK}\N{RIGHT SINGLE QUOTATION MARK}\N{LEFT DOUBLE QUOTATION MARK}\N{RIGHT DOUBLE QUOTATION MARK}]"
	r"|(?<=# )\N{BOX DRAWINGS LIGHT HORIZONTAL}"
)
""" Typography that marks text as AI-written: long dashes, ellipsis, arrows, curly quotes and box-drawing comment banners. """

# Functions
def check_cli() -> None:
	""" CLI entry point for the check command.
	Usage: stouputils check [path]...
	"""
	parser = argparse.ArgumentParser(
		prog="stouputils check",
		description="Report the style rules ruff cannot express, tuned by [tool.stouputils.check] in pyproject.toml.",
		epilog="Rules: " + ", ".join(RULES),
	)
	parser.add_argument(
		"paths", nargs="*", type=Path, default=[Path(".")], help="Files, or directories expanded to the files git does not ignore",
	)
	parser.add_argument(
		"--ignore", action="extend", type=lambda value: value.split(","), default=[], metavar="RULE[,RULE]",
		help="Rules to leave unchecked, on top of the pyproject ones",
	)
	parser.add_argument(
		"--final-newlines", action="extend", type=lambda value: value.split(","), default=[], metavar="SUFFIX=COUNT[,...]",
		help="Newline characters a file ends with, e.g. .py=1,.json=1, on top of the pyproject ones",
	)
	parser.add_argument(
		"--initial-newlines", action="extend", type=lambda value: value.split(","), default=[], metavar="SUFFIX=COUNT[,...]",
		help="Newline characters a file starts with, e.g. .md=1,.mcfunction=1, on top of the pyproject ones",
	)
	limits: list[str] = [field.name for field in fields(CheckConfig) if isinstance(field.default, int)]
	for name in limits:
		parser.add_argument(f"--{name.replace('_', '-')}", type=int, metavar="N", help="Replaces the pyproject value")
	arguments: argparse.Namespace = parser.parse_args()
	final_newlines: dict[str, int] = {suffix: int(count) for suffix, count in (entry.split("=") for entry in arguments.final_newlines)}
	initial_newlines: dict[str, int] = {
		suffix: int(count) for suffix, count in (entry.split("=") for entry in arguments.initial_newlines)
	}
	overrides: dict[str, int] = {name: value for name in limits if (value := getattr(arguments, name)) is not None}
	try:
		CheckConfig(ignore=arguments.ignore)
	except ValueError as error:
		parser.error(str(error))

	color: bool = sys.stdout.isatty()
	bold, cyan, red, green, reset = (Cfg.BOLD, Cfg.CYAN, Cfg.RED, Cfg.GREEN, Cfg.RESET) if color else ("",) * 5
	files: int = 0
	errors: int = 0
	for path in expand_paths(arguments.paths):
		base: CheckConfig = CheckConfig.for_directory(path.resolve().parent)
		config: CheckConfig = replace(
			base, ignore=[*base.ignore, *arguments.ignore], final_newlines={**base.final_newlines, **final_newlines},
			initial_newlines={**base.initial_newlines, **initial_newlines}, **overrides,
		)
		violations: list[Violation] = check_file(path, config)
		files += bool(violations)
		errors += len(violations)
		for violation in violations:
			location: str = f"{bold}{path}{reset}{cyan}:{reset}{violation.span}{cyan}:{reset}"
			print(f"{location} {red}{violation.rule}{reset} {violation.message}")
	if errors:
		print(f"{red}Found {errors} violation{'s' * (errors > 1)} in {files} file{'s' * (files > 1)}.{reset}")
		sys.exit(1)
	print(f"{green}All checks passed!{reset}")


def expand_paths(paths: Iterable[Path]) -> Iterator[Path]:
	""" Files as given, and every file under a directory that git tracks or does not ignore.

	Outside a git repository, a directory expands to every file below it whose path has no hidden part.
	"""
	for path in paths:
		if not path.is_dir():
			yield path
			continue
		command: list[str] = ["git", "-C", str(path), "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
		listing: subprocess.CompletedProcess[str] = subprocess.run(command, capture_output=True, text=True)
		if listing.returncode == 0:
			candidates: Iterable[Path] = (path / name for name in listing.stdout.split("\0") if name)
		else:
			candidates = (file for file in path.rglob("*") if not any(part.startswith(".") for part in file.relative_to(path).parts))
		yield from (file for file in candidates if file.is_file())


def check_file(path: Path, config: CheckConfig) -> list[Violation]:
	""" Every violation in a file that no suppression comment or ignored rule silences, sorted by line.

	Binary and non UTF-8 files yield nothing.
	"""
	with path.open("rb") as file:
		head: bytes = file.read(8192)
		if b"\0" in head:
			return []
		data: bytes = head + file.read()
	try:
		text: str = data.decode("utf-8")
	except UnicodeDecodeError:
		return []
	violations: list[Violation] = [
		Violation(text.count("\n", 0, found.start()) + 1, "banned-characters", f"{char!r} ({unicodedata.name(char)})")
		for found in BANNED_CHARACTERS.finditer(text)
		if (char := found.group())
	]
	silenced: list[Suppression] = []
	if path.suffix == ".py":
		violations += python_errors(text, config)
		silenced = suppressions(text)
	initial: str = text[:len(text) - len(text.lstrip("\r\n"))]
	expected: int | None = config.initial_newlines.get(path.suffix)
	if expected is not None and len(re.findall(r"\r\n|\r|\n", initial)) != expected:
		violations.append(Violation(1, "initial-newlines", f"must start with exactly {expected} newline characters"))
	expected: int | None = config.final_newlines.get(path.suffix)
	final: str = text[len(text.rstrip("\r\n")):]
	if expected and text and len(re.findall(r"\r\n|\r|\n", final)) != expected:
		violations.append(Violation(text.count("\n") or 1, "final-newlines", f"must end with exactly {expected} newline characters"))
	kept: list[Violation] = [violation for violation in violations if not any(s.covers(violation) for s in silenced)]
	ignored: set[str] = config.ignored_rules(path)
	return sorted(violation for violation in (*kept, *Suppression.unused(silenced, violations)) if violation.rule not in ignored)

