""" Editor-grade syntax highlighting for the Python code blocks of the generated documentation.

Two pieces are needed, and neither works without the other:
:mod:`.styles` supplies the VS Code palettes, and :mod:`.semantics` supplies the token distinctions those palettes
expect but that Pygments' Python lexer does not make on its own.

:func:`register` wires both into Sphinx and must run before the first page is highlighted, which is why the
generated ``conf.py`` calls it from its ``setup`` hook.
"""
# Imports
from typing import cast

from pygments.lexer import Lexer

from .semantics import CAMEL_CASE, DECLARATION_KEYWORDS, TYPE_BUILTINS, VSCodeSemanticFilter
from .styles import VSCodeDarkPlusStyle, VSCodeLightPlusStyle

__all__ = [
	"CAMEL_CASE",
	"DECLARATION_KEYWORDS",
	"TYPE_BUILTINS",
	"VSCodeDarkPlusStyle",
	"VSCodeLightPlusStyle",
	"VSCodeSemanticFilter",
	"register",
	"register_lexers",
	"register_styles",
]


# Functions
def register_styles() -> None:
	""" Make the two palettes resolvable by name, the way :func:`pygments.styles.get_style_by_name` expects.

	The ``pygments.styles`` entry points declared in ``pyproject.toml`` are the real mechanism, and the only one a
	consumer other than this generator will see.
	Filling the lookup tables directly costs two lines on top, and keeps a build working from a checkout whose
	installed metadata predates those entry points.
	"""
	# Pygments ships no type information for its style registry, and the lookup table is not part of its public API
	from pygments.styles import _STYLE_NAME_TO_MODULE_MAP, STYLE_MAP  # pyright: ignore[reportPrivateUsage, reportUnknownVariableType]
	by_module: dict[str, tuple[str, str]] = cast("dict[str, tuple[str, str]]", _STYLE_NAME_TO_MODULE_MAP)
	listed: dict[str, str] = cast("dict[str, str]", STYLE_MAP)
	for style in (VSCodeDarkPlusStyle, VSCodeLightPlusStyle):
		by_module.setdefault(style.name, (style.__module__, style.__name__))
		listed.setdefault(style.name, f"{style.__module__}::{style.__name__}")


def register_lexers() -> None:
	""" Install Python lexers carrying :class:`.VSCodeSemanticFilter` into Sphinx's lexer table.

	Sphinx narrows every Python language alias down to ``python``, or to ``pycon`` when the block opens on ``>>>``,
	then hands back any lexer registered under that name untouched.
	Filtering both therefore covers plain code blocks and doctests alike, and building them from Sphinx's own
	``lexer_classes`` keeps the options it would have applied, ``stripnl`` included.
	"""
	from sphinx.highlighting import lexer_classes, lexers
	for language in ("python", "pycon"):
		lexer: Lexer = lexer_classes[language]()
		lexer.add_filter(VSCodeSemanticFilter())  # pyright: ignore[reportUnknownMemberType]
		lexers[language] = lexer


def register() -> None:
	""" Register both the palettes and the filtered lexers. """
	register_styles()
	register_lexers()

