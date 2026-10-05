""" Run the Python or bash code block right above each demo image and render what the terminal shows as an animated SVG.

Run it with ``uv run --with pyte --with "fonttools[woff]" scripts/terminal_svg.py [name]...`` when a demo or the log format changes.
Naming SVGs (``print_module``) rewrites only those, the others keep their bytes.
"""

# Imports
import base64
import fcntl
import os
import pty
import re
import struct
import subprocess
import sys
import tempfile
import termios
import textwrap
import time
import urllib.request
from dataclasses import dataclass, replace
from pathlib import Path
from xml.sax.saxutils import escape, unescape

import pyte

# Constants
ROOT: Path = Path(__file__).resolve().parent.parent
COLUMNS: int = 104
ROWS: int = 200
""" Tall enough that a demo never scrolls, the SVG is cropped to the rows actually used. """
FONT_URL: str = "https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff2/FiraCode-Regular.woff2"
FONT_SIZE: float = 14
CHAR_WIDTH: float = FONT_SIZE * 0.6
LINE_HEIGHT: float = FONT_SIZE * 1.45
BASELINE: float = FONT_SIZE * 1.05
PADDING: float = 12
TITLE_BAR: float = 32
MIN_LOG_LINE_SECONDS: float = 0.35
""" Least delay between a log line (``[INFO 12:00:00] ...``) and the frame before it, so a burst of logs reads one by one. """
MIN_FRAME_SECONDS: float = 0.05
""" Other output closer than this to the frame before it joins that frame, so a report or a fast progress bar shows at once. """
ANSI_ESCAPE: re.Pattern[bytes] = re.compile(rb"\x1b\[[0-9;?]*[A-Za-z]")
CODE_BLOCK: re.Pattern[str] = re.compile(
	r"^```(?P<markdown_language>python|bash)\n(?P<markdown>.*?)^```"
	r"|^(?P<indent>[ \t]*)\.\. code-block:: (?P<rst_language>python|bash)\n\n(?P<rst>(?:(?P=indent)[ \t]+[^\n]*\n|[ \t]*\n)+)",
	re.M | re.S,
)
BACKGROUND: str = "#1e1e1e"
FOREGROUND: str = "#cccccc"
PALETTE: dict[str, str] = {
	"black": "#000000", "red": "#cd3131", "green": "#0dbc79", "brown": "#e5e510",
	"blue": "#2472c8", "magenta": "#bc3fbc", "cyan": "#11a8cd", "white": "#e5e5e5",
	"brightblack": "#666666", "brightred": "#f14c4c", "brightgreen": "#23d18b", "brightbrown": "#f5f543",
	"brightblue": "#3b8eea", "brightmagenta": "#d670d6", "brightcyan": "#29b8db", "brightwhite": "#e5e5e5",
}
""" VS Code's default dark terminal theme, keyed by pyte color names. """

# Classes
@dataclass(frozen=True)
class Demo:
	source: str
	svg: str
	title: str

@dataclass(frozen=True)
class Frame:
	start: float
	lines: tuple[str, ...]
	""" SVG markup of each screen row down to the last non-empty one. """

DEMOS: list[Demo] = [
	Demo(source="README.md", svg="assets/quick_start.svg", title="Quick start"),
	Demo(source="stouputils/all_doctests/__init__.py", svg="assets/all_doctests_module.svg", title="stouputils.all_doctests"),
	Demo(source="stouputils/archive/__init__.py", svg="assets/archive_module.svg", title="stouputils.archive"),
	Demo(source="stouputils/backup/__init__.py", svg="assets/backup_module.svg", title="stouputils.backup"),
	Demo(source="stouputils/check/__init__.py", svg="assets/check_module.svg", title="stouputils.check"),
	Demo(source="stouputils/collections/__init__.py", svg="assets/collections_module.svg", title="stouputils.collections"),
	Demo(source="stouputils/compression/__init__.py", svg="assets/compression_module.svg", title="stouputils.compression"),
	Demo(
		source="stouputils/continuous_delivery/__init__.py",
		svg="assets/continuous_delivery_module.svg",
		title="stouputils.continuous_delivery",
	),
	Demo(source="stouputils/ctx/__init__.py", svg="assets/ctx_module.svg", title="stouputils.ctx"),
	Demo(source="stouputils/decorators/__init__.py", svg="assets/decorators_module.svg", title="stouputils.decorators"),
	Demo(source="stouputils/image/__init__.py", svg="assets/image_module.svg", title="stouputils.image"),
	Demo(source="stouputils/installer/__init__.py", svg="assets/installer_module.svg", title="stouputils.installer"),
	Demo(source="stouputils/io/__init__.py", svg="assets/io_module.svg", title="stouputils.io"),
	Demo(source="stouputils/lock/__init__.py", svg="assets/lock_module.svg", title="stouputils.lock"),
	Demo(source="stouputils/mlflow/__init__.py", svg="assets/mlflow_module.svg", title="stouputils.mlflow"),
	Demo(source="stouputils/parallel/__init__.py", svg="assets/parallel_module.svg", title="stouputils.parallel"),
	Demo(source="stouputils/print/__init__.py", svg="assets/print_module.svg", title="stouputils.print"),
	Demo(source="stouputils/system.py", svg="assets/system_module.svg", title="stouputils.system"),
	Demo(source="stouputils/typing/__init__.py", svg="assets/typing_module.svg", title="stouputils.typing"),
	Demo(source="stouputils/version_pkg.py", svg="assets/version_pkg_module.svg", title="stouputils.version_pkg"),
	Demo(
		source="stouputils/continuous_delivery/pyproject.py",
		svg="assets/increment_version_from_pyproject.svg",
		title="stp.increment_version_from_pyproject()",
	),
	Demo(source="stouputils/io/redirect.py", svg="assets/copytree_with_progress.svg", title="stp.copytree_with_progress()"),
	Demo(source="stouputils/io/redirect.py", svg="assets/redirect_folder.svg", title="stp.redirect_folder()"),
	Demo(source="stouputils/parallel/subprocess.py", svg="assets/run_in_subprocess.svg", title="stp.run_in_subprocess()"),
	Demo(source="stouputils/print/color_formatting.py", svg="assets/colored.svg", title="stp.colored()"),
]

# Functions
def main() -> None:
	with tempfile.TemporaryDirectory() as folder:
		font: Path = Path(folder) / "FiraCode-Regular.woff2"
		urllib.request.urlretrieve(FONT_URL, font)
		for demo in [demo for demo in DEMOS if any(name in demo.svg for name in sys.argv[1:] or [""])]:
			text: str = (ROOT / demo.source).read_text(encoding="utf-8")
			*_, block = CODE_BLOCK.finditer(text[:text.index(demo.svg)])
			language: str = block["markdown_language"] or block["rst_language"]
			frames: list[Frame] = to_frames(record(block["markdown"] or textwrap.dedent(block["rst"]), language))
			(ROOT / demo.svg).write_text(render(frames, demo.title, font), encoding="utf-8")
			print(f"{demo.svg}: {len(frames)} frames")

def record(code: str, language: str) -> list[tuple[float, bytes]]:
	""" Run the code in a pseudo-terminal and return its output chunks with their time since launch, in seconds. """
	with tempfile.TemporaryDirectory() as folder:
		script: Path = Path(folder) / "demo"
		script.write_text(code, encoding="utf-8")
		master, slave = pty.openpty()
		fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLUMNS, 0, 0))
		interpreter: str = sys.executable if language == "python" else language
		process = subprocess.Popen([interpreter, script], stdin=slave, stdout=slave, stderr=slave, cwd=folder)
		os.close(slave)
		start: float = time.monotonic()
		chunks: list[tuple[float, bytes]] = []
		while True:
			try:
				data: bytes = os.read(master, 65536)
			except OSError:  # EIO once every process holding the terminal has exited
				break
			chunks.append((time.monotonic() - start, data))
		os.close(master)
		if process.wait():
			print(f"Exit code {process.returncode}, check the SVG shows what the demo means to")
		return chunks

def to_frames(chunks: list[tuple[float, bytes]]) -> list[Frame]:
	""" Replay the output in a terminal emulator, one frame per chunk and per log line, paced by MIN_LOG_LINE_SECONDS. """
	screen = pyte.Screen(COLUMNS, ROWS)
	stream = pyte.ByteStream(screen)
	frames: list[Frame] = []
	for start, data in chunks:
		for piece in data.splitlines(keepends=True):
			stream.feed(piece)
			lines: tuple[str, ...] = screen_lines(screen)
			if frames and lines == frames[-1].lines:
				continue
			is_log_line: bool = ANSI_ESCAPE.sub(b"", piece).lstrip(b"\r").startswith(b"[")
			if frames and not is_log_line and start < frames[-1].start + MIN_FRAME_SECONDS:
				frames[-1] = replace(frames[-1], lines=lines)
				continue
			least: float = MIN_LOG_LINE_SECONDS if is_log_line else 0
			frames.append(Frame(start=max(start, frames[-1].start + least) if frames else start, lines=lines))
	return frames

def screen_lines(screen: pyte.Screen) -> tuple[str, ...]:
	rows: list[str] = [render_row(screen.buffer[y]) for y in range(screen.cursor.y + 1)]
	while rows and not rows[-1]:
		rows.pop()
	return tuple(rows)

def render_row(row: dict[int, pyte.screens.Char]) -> str:
	""" SVG text elements of one screen row, one per run of characters sharing a style. """
	cells: list[pyte.screens.Char] = [row[x] for x in range(COLUMNS)]
	while cells and cells[-1].data == " ":
		cells.pop()
	elements: list[str] = []
	x: int = 0
	while x < len(cells):
		end: int = x + 1
		while end < len(cells) and (cells[end].fg, cells[end].bold) == (cells[x].fg, cells[x].bold):
			end += 1
		text: str = "".join(cell.data for cell in cells[x:end]).replace(" ", "\N{NO-BREAK SPACE}")
		fill: str = PALETTE.get(cells[x].fg, FOREGROUND if cells[x].fg == "default" else f"#{cells[x].fg}")
		weight: str = ' font-weight="bold"' if cells[x].bold else ""
		elements.append(
			f'<text x="{x * CHAR_WIDTH:.1f}" textLength="{(end - x) * CHAR_WIDTH:.1f}" fill="{fill}"{weight}>{escape(text)}</text>'
		)
		x = end
	return "".join(elements)

def render(frames: list[Frame], title: str, font: Path) -> str:
	""" One SVG where every frame sits below the previous one and a stepped animation slides them through the window once. """
	frame_height: float = max(len(frame.lines) for frame in frames) * LINE_HEIGHT
	width: float = COLUMNS * CHAR_WIDTH + 2 * PADDING
	height: float = TITLE_BAR + frame_height + PADDING
	duration: float = frames[-1].start

	symbols: dict[str, str] = {}
	film: list[str] = []
	for index, frame in enumerate(frames):
		for y, line in enumerate(frame.lines):
			if line:
				symbol: str = symbols.setdefault(line, f"l{len(symbols)}")
				film.append(f'<use href="#{symbol}" y="{index * frame_height + y * LINE_HEIGHT + BASELINE:.1f}"/>')
	keyframes: str = "".join(
		f"{100 * frame.start / duration:.3f}%{{transform:translateY({-index * frame_height:.1f}px)}}"
		for index, frame in enumerate(frames)
	)
	shown: str = title + "".join(unescape(re.sub(r"<[^>]+>", "", line)) for line in symbols)
	return "".join([
		f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}"',
		f' font-family="Fira Code, monospace" font-size="{FONT_SIZE}"><style>',
		f"@font-face{{font-family:'Fira Code';src:url(data:font/woff2;base64,{subset_font(font, shown)}) format('woff2')}}",
		f".film{{animation:play {duration:.2f}s step-end forwards}}@keyframes play{{{keyframes}}}",
		"@media (prefers-reduced-motion:reduce){",
		f".film{{animation:none;transform:translateY({-(len(frames) - 1) * frame_height:.1f}px)}}}}</style><defs>",
		*(f'<g id="{symbol}">{line}</g>' for line, symbol in symbols.items()),
		f'<clipPath id="screen"><rect width="{width - 2 * PADDING:.1f}" height="{frame_height:.1f}"/></clipPath></defs>',
		f'<rect width="{width:.1f}" height="{height:.1f}" rx="8" fill="{BACKGROUND}" stroke="#ffffff30"/>',
		'<circle cx="20" cy="16" r="6" fill="#ff5f57"/>',
		'<circle cx="40" cy="16" r="6" fill="#febc2e"/>',
		'<circle cx="60" cy="16" r="6" fill="#28c840"/>',
		f'<text x="{width / 2:.1f}" y="21" fill="#999999" text-anchor="middle">{escape(title)}</text>',
		f'<g transform="translate({PADDING} {TITLE_BAR})" clip-path="url(#screen)"><g class="film">{"".join(film)}</g></g>',
		"</svg>\n",
	])

def subset_font(font: Path, text: str) -> str:
	""" Base64 WOFF2 of the font reduced to the characters of the text, without the ligatures that turn ``...`` into one glyph. """
	output: Path = font.with_suffix(".subset.woff2")
	subprocess.run(
		[
			sys.executable, "-m", "fontTools.subset", font, f"--text={text}",
			"--layout-features=", "--flavor=woff2", f"--output-file={output}",
		],
		check=True,
	)
	return base64.b64encode(output.read_bytes()).decode()


if __name__ == "__main__":
	main()

