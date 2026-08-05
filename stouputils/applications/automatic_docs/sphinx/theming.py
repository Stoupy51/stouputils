""" Theme, syntax highlighting and stylesheet concerns of the generated documentation.

Pygments' Python lexer is coarse: it only tags an identifier as ``Name.Function`` or ``Name.Class`` when a literal
``def`` or ``class`` introduces it, and emits a bare ``Name`` for every call, attribute, argument and variable.
A palette designed for a finer grammar therefore paints most of the code in whichever colour it gave ``Name``.
That is why the styles below are picked so that ``Name`` keeps the foreground colour, leaving hues for the tokens
the lexer genuinely recognises.
"""
# Imports
import importlib

from ....io.path import super_open
from ..common import check_base_dependencies

# Constants
DEFAULT_LIGHT_STYLE: str = "a11y-high-contrast-light"
""" Pygments style for light mode, keeping ``Name`` at the foreground colour and reaching 7.4:1 minimum contrast. """

DEFAULT_DARK_STYLE: str = "github-dark"
""" Pygments style for dark mode.

Its high-contrast sibling, which is the theme's own default, paints ``Name`` in ``#DBB7FF``.
Since a Python page emits about a hundred bare ``Name`` tokens for each ``def``, that turns whole snippets violet.
"""

CUSTOM_CSS: str = """
/* Custom CSS for Sphinx documentation */
/* Reduce heading sizes */
h1 { font-size: 2.0em !important; }
h2 { font-size: 1.6em !important; }
h3 { font-size: 1.4em !important; }
h4 { font-size: 1.2em !important; }
h5 { font-size: 1.0em !important; }
h6 { font-size: 0.9em !important; }

/* Gradient animation keyframes */
@keyframes shine-slide {
	0% { background-position: -200% center; }
	100% { background-position: 200% center; }
}

/* Adjustments to abmonition */
.admonition {
	text-decoration: none;
	padding: 1rem;
	display: block;
}

/* On hover animation for various elements */
a, h1, h2, h3, h4, h5, h6, .admonition {
	transition: transform 0.3s;
}

a:hover, h1:hover, h2:hover, h3:hover, h4:hover, h5:hover, h6:hover, .admonition:hover {
	transform: scale(1.05);
}
a:hover, a:hover span {
	background: linear-gradient(
		110deg,
		currentColor 0%,
		currentColor 40%,
		white 50%,
		currentColor 60%,
		currentColor 100%
	);
	background-size: 200% 100%;
	background-clip: text;
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
	animation: shine-slide 3.5s linear infinite;
}

/* The light palette leaves doctest prompts and outputs uncoloured, so a doctest reads as one flat block. */
/* The dark palette defines both, and its html[data-theme="dark"] prefix outranks these rules untouched. */
.highlight .gp { color: #6a737d; user-select: none; }
.highlight .go { color: #444d56; font-style: italic; }
"""
""" Stylesheet written to ``_static/custom.css`` and loaded on top of the theme. """


# Functions
def check_dependencies(html_theme: str) -> None:
	""" Check that the requested theme, and every base requirement, is installed.

	Args:
		html_theme (str): HTML theme used by the documentation, ex: "breeze", "pydata_sphinx_theme", "furo"
	Raises:
		ImportError: If the theme or any base requirement is missing
	"""
	check_base_dependencies()
	if html_theme == "breeze":
		html_theme = "sphinx_breeze_theme"
	try:
		importlib.import_module(html_theme)
	except ImportError as e:
		raise ImportError(f"{html_theme} is not installed. Please add it to your dependencies.") from e


def get_theme_options(html_theme: str, default_mode: str) -> dict[str, str | bool]:
	""" Build the ``html_theme_options`` mapping, holding only keys the chosen theme understands.

	``default_mode`` reaches breeze through ``html_theme_options``, and pydata through ``html_context``.
	Passing it to a theme that knows neither only earns an "unsupported theme option" warning, so it is filtered here.

	Args:
		html_theme   (str): HTML theme used by the documentation
		default_mode (str): Colour mode a first-time visitor gets, one of "auto", "light" or "dark"
	Returns:
		dict[str, str | bool]: Options to write into the generated ``conf.py``

	Examples:
		>>> get_theme_options("breeze", "dark")
		{'navigation_with_keys': True, 'default_mode': 'dark'}
		>>> get_theme_options("furo", "dark")
		{'navigation_with_keys': True}
	"""
	options: dict[str, str | bool] = {"navigation_with_keys": True}
	if html_theme == "breeze":
		options["default_mode"] = default_mode
	return options


def write_custom_css(static_dir: str) -> None:
	""" Write :data:`CUSTOM_CSS` into the static folder the generated ``conf.py`` points at.

	Args:
		static_dir (str): The ``docs/source/_static`` folder
	"""
	with super_open(f"{static_dir}/custom.css", "w") as f:
		f.write(CUSTOM_CSS)

