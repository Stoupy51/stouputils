""" Docstring normalization applied before Sphinx parses the output of autodoc.

reStructuredText only recognizes a doctest block when it starts a new block, which means a blank line
must separate it from the prose introducing it.
A docstring written without that blank line gets folded into the preceding paragraph, so the ``>>>``
lines render as plain text (smart quotes included) instead of a highlighted code block.
:func:`fix_doctest_blocks` inserts the missing blank lines and :func:`connect_docstring_fixes` wires it
to the ``autodoc-process-docstring`` event, so the fix applies to every documented object at once.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ...lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import re
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
	Examples:
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
		if verbatim_indent is not None:
			if indent > verbatim_indent:
				previous_is_blank = False
				result.append(line)
				continue
			verbatim_indent = None

		if stripped.startswith(">>>"):
			if not in_doctest and not previous_is_blank:
				result.append("")
			in_doctest = True
		elif not in_doctest:
			directive: re.Match[str] | None = DIRECTIVE_PATTERN.match(stripped)
			if stripped.endswith("::") or (directive is not None and directive.group(1) in VERBATIM_DIRECTIVES):
				verbatim_indent = indent

		previous_is_blank = False
		result.append(line)

	return result

def process_docstring(app: Any, what: str, name: str, obj: Any, options: Any, lines: list[str]) -> None:
	""" Handler for the ``autodoc-process-docstring`` event, editing `lines` in place as Sphinx requires.

	Args:
		app:     The Sphinx application, unused
		what:    The type of the documented object, unused
		name:    The fully qualified name of the documented object, unused
		obj:     The documented object itself, unused
		options: The autodoc directive options, unused
		lines:   Docstring lines, modified in place
	Examples:
		>>> lines = ["Intro", ">>> 1 + 1", "2"]
		>>> process_docstring(None, "class", "Demo", None, None, lines)
		>>> lines
		['Intro', '', '>>> 1 + 1', '2']
	"""
	lines[:] = fix_doctest_blocks(lines)

def connect_docstring_fixes(app: Any) -> None:
	""" Register the docstring fixes on a Sphinx application.

	Connected with a low priority so it runs after napoleon has expanded the Google style sections into
	reStructuredText, which is what actually gets parsed.

	Args:
		app: The Sphinx application to connect the handler to
	"""
	app.connect("autodoc-process-docstring", process_docstring, priority=800)

