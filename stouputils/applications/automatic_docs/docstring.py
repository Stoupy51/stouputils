""" Docstring normalization applied before Sphinx parses the output of autodoc.

reStructuredText only recognizes a doctest block when it starts a new block, which means a blank line
must separate it from the prose introducing it.
A docstring written without that blank line gets folded into the preceding paragraph,
so the ``>>>`` lines render as plain text (smart quotes included) instead of a highlighted code block.
:func:`fix_doctest_blocks` inserts the missing blank lines and :func:`connect_docstring_fixes` wires it
to the ``autodoc-process-docstring`` event, so the fix applies to every documented object at once.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ...lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import re
import unicodedata
from typing import Any

# Constants
VERBATIM_DIRECTIVES: frozenset[str] = frozenset({
	"code", "code-block", "sourcecode", "literalinclude", "parsed-literal",
	"doctest", "testcode", "testsetup", "testcleanup", "math", "raw",
})
""" Directives whose body is taken verbatim, so ``>>>`` lines inside them must be left untouched. """

DIRECTIVE_PATTERN: re.Pattern[str] = re.compile(r"^\.\.[ \t]+([\w-]+)::")
""" Matches the opening line of a reStructuredText directive, capturing its name. """


# Functions
def fix_doctest_blocks(lines: list[str]) -> list[str]:
	""" Insert the blank line reStructuredText needs before a doctest block that follows prose.

	Lines inside a verbatim region (a literal block introduced by ``::`` or a directive from
	``VERBATIM_DIRECTIVES``) are copied as-is, since their ``>>>`` already renders correctly and an
	extra blank line would truncate the block.

	Args:
		lines: Docstring lines, without trailing newlines
	Returns:
		The same lines with a blank line before every doctest block that lacked one
	>>> fix_doctest_blocks(["Building resource locations", ">>> 1 + 1", "2"])
	['Building resource locations', '', '>>> 1 + 1', '2']

	>>> fix_doctest_blocks(["Already fine", "", ">>> 1 + 1", "2"])
	['Already fine', '', '>>> 1 + 1', '2']

	>>> fix_doctest_blocks([">>> a = 1", ">>> a", "1"])
	['>>> a = 1', '>>> a', '1']

	>>> fix_doctest_blocks(["Intro:", "", ">>> 1", "1", ">>> 2", "2"])
	['Intro:', '', '>>> 1', '1', '>>> 2', '2']

	>>> fix_doctest_blocks([".. code-block:: python", "", "    Header", "    >>> 1 + 1"])
	['.. code-block:: python', '', '    Header', '    >>> 1 + 1']

	>>> fix_doctest_blocks(["Sample::", "", "    Header", "    >>> 1 + 1"])
	['Sample::', '', '    Header', '    >>> 1 + 1']
	"""
	result: list[str] = []
	in_doctest: bool = False
	previous_is_blank: bool = True
	verbatim_indent: int | None = None

	for line in lines:
		stripped: str = line.strip()

		# A blank line closes a doctest block, but not a verbatim region (those may contain blank lines)
		if not stripped:
			in_doctest = False
			previous_is_blank = True
			result.append(line)
			continue

		# A verbatim region lasts until a line dedents back to the indentation of its introducer
		indent: int = len(line) - len(line.lstrip())
		if verbatim_indent is not None and indent > verbatim_indent:
			previous_is_blank = False
			result.append(line)
			continue
		verbatim_indent = None

		if stripped.startswith(">>>"):
			if not in_doctest and not previous_is_blank:
				result.append("")
			in_doctest = True
		elif not in_doctest and opens_verbatim(stripped):
			verbatim_indent = indent

		previous_is_blank = False
		result.append(line)

	return result

def opens_verbatim(stripped: str) -> bool:
	""" Whether a stripped docstring line opens a verbatim region, with a trailing ``::`` or a directive from ``VERBATIM_DIRECTIVES``.

	>>> opens_verbatim("Sample::"), opens_verbatim(".. code-block:: python"), opens_verbatim("Plain prose.")
	(True, True, False)
	"""
	directive: re.Match[str] | None = DIRECTIVE_PATTERN.match(stripped)
	return stripped.endswith("::") or (directive is not None and directive.group(1) in VERBATIM_DIRECTIVES)

def leading_emoji(text: str | None) -> str:
	""" The emoji a text opens with, empty when it opens with anything else.

	>>> leading_emoji("🖨️ Printing helpers"), leading_emoji("Printing helpers"), leading_emoji(None)
	('🖨️', '', '')
	"""
	first_word: str = next(iter((text or "").split()), "")
	return first_word if first_word and unicodedata.category(first_word[0]) == "So" else ""

def process_docstring(app: Any, what: str, name: str, obj: Any, options: Any, lines: list[str]) -> None:
	""" Handler for the ``autodoc-process-docstring`` event, editing `lines` in place as Sphinx requires.

	The emoji opening a module docstring is dropped, since the title of the module's page or section already shows it.

	Args:
		what:  The type of the documented object
		lines: Docstring lines, modified in place
	>>> lines = ["Intro", ">>> 1 + 1", "2"]
	>>> process_docstring(None, "class", "Demo", None, None, lines)
	>>> lines
	['Intro', '', '>>> 1 + 1', '2']
	>>> lines = ["📝 Typing helpers"]
	>>> process_docstring(None, "module", "typing", None, None, lines)
	>>> lines
	['Typing helpers']
	"""
	if what == "module" and lines and (emoji := leading_emoji(lines[0])):
		lines[0] = lines[0].removeprefix(emoji).lstrip()
	lines[:] = fix_doctest_blocks(lines)

def keep_attribute_docstring_whole(app: Any, what: str, name: str, obj: Any, options: Any, lines: list[str]) -> None:
	""" Handler for ``autodoc-process-docstring`` keeping napoleon from reading a type out of an attribute docstring.

	Napoleon takes whatever precedes the first colon of an attribute docstring as its type, ``minecraft`` in
	"The ore item, `minecraft:emerald`". A leading colon gives it an empty type, and the whole line as description.

	Args:
		what:  The type of the documented object
		lines: Docstring lines, modified in place
	>>> lines = ["The ore item, `minecraft:emerald`"]
	>>> keep_attribute_docstring_whole(None, "data", "ORE", None, None, lines)
	>>> lines
	[': The ore item, `minecraft:emerald`']
	"""
	if what in {"attribute", "data", "property"} and lines and lines[0]:
		lines[0] = f": {lines[0]}"

def connect_docstring_fixes(app: Any) -> None:
	""" Register the docstring fixes on a Sphinx application.

	:func:`keep_attribute_docstring_whole` runs before napoleon, and :func:`process_docstring` after it,
	once the Google style sections are expanded into the reStructuredText that actually gets parsed.

	Args:
		app: The Sphinx application to connect the handlers to
	"""
	app.connect("autodoc-process-docstring", keep_attribute_docstring_whole, priority=400)
	app.connect("autodoc-process-docstring", process_docstring, priority=800)

