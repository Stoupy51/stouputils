""" Rules on Python sources: indentation, comments, docstrings and module constants. """

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import ast
import io
import re
import tokenize
from collections.abc import Iterable, Iterator
from dataclasses import replace
from itertools import pairwise

from .rules import CheckConfig, Suppression, Violation

# Constants
CLAUSE_ENDINGS: tuple[str, ...] = (".", "!", "?", ":", ";", ",")
""" Line endings that close a sentence or a clause, where a line break reads naturally. """

CLAUSE_BOUNDARY: re.Pattern[str] = re.compile(r"[.!?:;,](?:\s|$)")
""" Punctuation followed by a space, which splits a line into its clauses. """

NEW_ITEM: re.Pattern[str] = re.compile(
	r"\*{0,2}\w+(?:\s+\([^)]*\))?:(?:\s|$)"
	r"|\w+(?:\[.*?\])?(?: \| \w+(?:\[.*?\])?)+:\s"
	r"|\w[.)]\s"
	r"|(?:noqa|type:|pyright:|ruff:|fmt:|pragma|stp:|stouputils:)"
)
""" Line starts that open an entry of their own: an ``Args:`` entry, a union type, a list item, or a tool directive. """

EXAMPLES_HEADER: re.Pattern[str] = re.compile(r"\s*Examples?:\s*$")
""" Header that doctests do not need, since ``>>>`` already marks them. """

TYPED_ARGUMENT: re.Pattern[str] = re.compile(r"\s*\*{0,2}(?!Traceback\b)\w+:?\s+\(.*\):")
""" ``Args:`` entry that repeats the type the signature already carries, as in ``name (int):``. """

SPAN_DELIMITERS: tuple[str, ...] = ("``", "`", '"')
""" Delimiters of inline code and quotes, the double backtick counted and removed before the single one. """

STRANDED_FRAGMENT: str = "a line break leaves a few words of a clause alone, break at a clause or sentence boundary"
""" Message shared by comments and docstrings. """

SUPPRESSION: re.Pattern[str] = re.compile(r"#\s*(stp|stouputils):\s*ignore\b(?:\[([^\]]*)\])?")
""" A suppression comment: ``stp`` silences its own line, or the string it closes, and ``stouputils`` the whole file. """

LAYOUT_TOKENS: frozenset[int] = frozenset({tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER})
""" Tokens carrying no code, which a suppression comment never attaches to. """

# Functions
def python_errors(source: str, config: CheckConfig) -> Iterator[Violation]:
	""" Violations of the Python rules, in no particular order.

	>>> rules = lambda source: sorted((v.line, v.rule) for v in python_errors(source, CheckConfig()))
	>>> rules("def f():\\n\\tx  = 1\\n\\ty\\t= 2\\n")
	[(3, 'space-alignment')]
	>>> rules("x = [\\n    1,\\n]\\n"), rules('x = f\"\"\"\\n    {1}\\n\"\"\"\\n')
	([(2, 'tab-indentation')], [])
	>>> [(v.line, v.end_line) for v in python_errors("if x:\\n    a = 1\\n\\n    b = 2\\n", CheckConfig())]
	[(2, 4)]
	>>> rules("# Roll once per tick. The\\n# caller resets the counter.\\n")
	[(2, 'stranded-fragment')]
	>>> rules("LIMIT: int = 3  # Retries\\n")
	[(1, 'constant-comment')]
	"""
	try:
		tokens: list[tokenize.TokenInfo] = list(tokenize.generate_tokens(io.StringIO(source).readline))
		tree: ast.Module = ast.parse(source)
	except (SyntaxError, tokenize.TokenError) as error:
		yield Violation(1, "syntax-error", f"cannot parse: {error}")
		return
	yield from indentation_errors(source, string_content_lines(tokens), tab_aligned_lines(tokens))
	yield from comment_errors(tokens, config)
	yield from docstring_layout_errors(tree, config)
	yield from constant_errors(tree, tokens)
	for node in statements(tree):
		if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
			yield from docstring_errors(node.value.value, node.lineno, config)


def suppressions(source: str) -> list[Suppression]:
	""" Suppression comments of a Python source, none when it does not tokenize.

	A ``stp`` comment after a multi-line string covers the whole string, the only way to reach the lines of a docstring.

	>>> [(s.line, s.lines) for s in suppressions("def f():\\n\\t'''\\n\\tlong\\n\\t'''  # stp: ignore[long-docstring]\\n")]
	[(4, range(2, 5))]
	>>> suppressions("# stouputils: ignore[tab-indentation, long-comment]\\n")
	[Suppression(line=1, rules=('tab-indentation', 'long-comment'), lines=None)]
	>>> suppressions('x = "# stp: ignore[long-comment]"  # stp: ignore\\n')
	[Suppression(line=1, rules=(), lines=range(1, 2))]
	"""
	try:
		tokens: list[tokenize.TokenInfo] = list(tokenize.generate_tokens(io.StringIO(source).readline))
	except (SyntaxError, tokenize.TokenError):
		return []
	found: list[Suppression] = []
	opened: list[int] = []
	code_start: int = 0
	code_end: int = 0
	for token in tokens:
		kind: str = tokenize.tok_name[token.type]
		if token.type == tokenize.COMMENT and (match := SUPPRESSION.search(token.string)):
			line: int = token.start[0]
			found.append(suppression_from_comment(match, line, statement_start=code_start if code_end == line else line))
		if kind.endswith("STRING_START"):
			opened.append(token.start[0])
		if token.type != tokenize.COMMENT and token.type not in LAYOUT_TOKENS:
			code_start, code_end = (opened.pop() if kind.endswith("STRING_END") else token.start[0]), token.end[0]
	return found


def suppression_from_comment(match: re.Match[str], line: int, statement_start: int) -> Suppression:
	""" The suppression a comment matching ``SUPPRESSION`` declares.

	Args:
		line:            Line of the comment.
		statement_start: First line of the statement the comment ends, which a ``stp`` comment covers down to its own line.

	>>> suppression_from_comment(SUPPRESSION.search("# stp: ignore[long-comment, x]"), 5, statement_start=3)
	Suppression(line=5, rules=('long-comment', 'x'), lines=range(3, 6))
	"""
	rules: tuple[str, ...] = tuple(rule.strip() for rule in (match.group(2) or "").split(",") if rule.strip())
	return Suppression(line=line, rules=rules, lines=None if match.group(1) == "stouputils" else range(statement_start, line + 1))


def statements(tree: ast.Module) -> Iterator[ast.stmt]:
	""" Every statement of a module, nested ones included, without descending into expressions. """
	stack: list[ast.AST] = [tree]
	while stack:
		node: ast.AST = stack.pop()
		if isinstance(node, ast.stmt):
			yield node
		stack.extend(child for field in ("body", "orelse", "finalbody", "handlers", "cases") for child in getattr(node, field, ()))


def indentation_errors(source: str, string_lines: set[int], tab_aligned: set[int]) -> Iterator[Violation]:
	""" Lines of code indented with a space, or aligned with a tab between two tokens, one violation per run of them.

	Lines continuing a multi-line string are data, so they are left alone, and neither they nor blank lines end a run.
	"""
	run: Violation | None = None
	for number, line in enumerate(source.splitlines(), start=1):
		content: str = line.lstrip(" \t")
		if not content or number in string_lines:
			continue
		violation: Violation | None = None
		if " " in line[:len(line) - len(content)]:
			violation = Violation(number, "tab-indentation", "space in indentation, indent with tabs")
		elif number in tab_aligned:
			violation = Violation(number, "space-alignment", "tab after the first character, align with spaces")
		if run and violation and violation.rule == run.rule:
			run = replace(run, end_line=number)
			continue
		if run:
			yield run
		run = violation
	if run:
		yield run


def tab_aligned_lines(tokens: list[tokenize.TokenInfo]) -> set[int]:
	""" Lines where a tab separates two tokens, which leaves the tabs inside strings and comments alone. """
	return {
		token.start[0]
		for previous, token in pairwise(tokens)
		if previous.end[0] == token.start[0] and "\t" in token.line[previous.end[1]:token.start[1]]
	}


def string_content_lines(tokens: list[tokenize.TokenInfo]) -> set[int]:
	""" Lines whose leading whitespace belongs to a multi-line string rather than to the code. """
	string_lines: set[int] = set()
	string_starts: list[int] = []
	for token in tokens:
		kind: str = tokenize.tok_name[token.type]
		if kind.endswith("STRING_START"):
			string_starts.append(token.start[0])
		elif kind.endswith("STRING_END"):
			string_lines.update(range(string_starts.pop() + 1, token.end[0] + 1))
		elif kind == "STRING":
			string_lines.update(range(token.start[0] + 1, token.end[0] + 1))
	return string_lines


def comment_errors(tokens: list[tokenize.TokenInfo], config: CheckConfig) -> Iterator[Violation]:
	""" Blocks of comment lines over the limit, and fragments stranded across comment lines. """
	comments: list[tuple[int, int, str]] = [
		(token.start[0], token.start[1], token.string.lstrip("#").strip())
		for token in tokens
		if token.type == tokenize.COMMENT and not token.line[:token.start[1]].strip()
	]
	block_start: int = 0
	for index, (number, column, text) in enumerate(comments):
		previous_number, previous_column, previous_text = comments[index - 1]
		if index == 0 or previous_number != number - 1 or previous_column != column:
			block_start = index
			continue
		if strands_fragment(previous_text, text, config.fragment_max_words):
			yield Violation(number, "stranded-fragment", STRANDED_FRAGMENT)
		if index - block_start == config.comment_max_lines:
			message: str = f"comment longer than {config.comment_max_lines} lines, keep one line per comment"
			yield Violation(comments[block_start][0], "long-comment", message)
	yield from split_spans((number, text) for number, _, text in comments)


def docstring_layout_errors(tree: ast.Module, config: CheckConfig) -> Iterator[Violation]:
	""" A module docstring below line 1, and function or class docstrings over the size limit. """
	if tree.body and is_docstring(tree.body[0]) and tree.body[0].lineno != 1:
		yield Violation(tree.body[0].lineno, "module-docstring-position", "module docstring must be on line 1")
	for node in statements(tree):
		if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) and is_docstring(docstring := node.body[0]):
			length: int = (docstring.end_lineno or docstring.lineno) - docstring.lineno + 1
			limit: int = config.docstring_max_lines
			if length > limit:
				yield Violation(docstring.lineno, "long-docstring", f"docstring of {length} lines, the limit is {limit}")


def constant_errors(tree: ast.Module, tokens: list[tokenize.TokenInfo]) -> Iterator[Violation]:
	""" Module constants documented by a trailing comment rather than a docstring below them. """
	trailing_comments: set[int] = {
		token.start[0]
		for token in tokens
		if token.type == tokenize.COMMENT
		and token.line[:token.start[1]].strip()
		and not NEW_ITEM.match(token.string.lstrip("#").strip())
	}
	for node in tree.body:
		if not isinstance(node, ast.Assign | ast.AnnAssign):
			continue
		target: ast.expr = node.target if isinstance(node, ast.AnnAssign) else node.targets[0]
		if isinstance(target, ast.Name) and target.id.isupper() and node.end_lineno in trailing_comments:
			yield Violation(node.lineno, "constant-comment", "constant documented by a trailing comment, put a docstring below it")


def is_docstring(node: ast.stmt) -> bool:
	""" Whether a statement is a bare string literal. """
	return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


def docstring_errors(docstring: str, first_line: int, config: CheckConfig) -> Iterator[Violation]:
	""" An ``Examples:`` header, types repeated in ``Args:``, and fragments stranded across lines.

	Code blocks and doctests are skipped, and a deeper indent continues an entry rather than a sentence.

	>>> [v.rule for v in docstring_errors("Args:\\n\\tlimit (int): Retries\\nExamples:\\n\\t>>> f()", 1, CheckConfig())]
	['typed-argument', 'examples-header']
	"""
	previous: str = ""
	previous_indent: int = 0
	code_indent: int | None = None
	prose: list[tuple[int, str]] = []
	for number, line in enumerate(docstring.splitlines(), start=first_line):
		content: str = line.strip()
		indent: int = len(line) - len(line.lstrip())
		if EXAMPLES_HEADER.match(line):
			yield Violation(number, "examples-header", "'Examples:' header, put the >>> lines straight in the docstring")
		if TYPED_ARGUMENT.match(line):
			yield Violation(number, "typed-argument", "type repeated in Args, the signature already carries it")
		if code_indent is not None and (not content or indent > code_indent):
			continue
		code_indent = code_block_indent(content, indent)
		prose.append((number, content))
		same_block: bool = bool(previous) and indent == previous_indent and code_indent is None
		if same_block and strands_fragment(previous, content, config.fragment_max_words):
			yield Violation(number, "stranded-fragment", STRANDED_FRAGMENT)
		previous, previous_indent = content, indent
	yield from split_spans(prose)


def split_spans(lines: Iterable[tuple[int, str]]) -> Iterator[Violation]:
	""" Inline code or a quote opened on one line and closed on a later one, reported at the line opening it.

	>>> [v.line for v in split_spans([(1, "use ``f(a,"), (2, "b)`` here"), (3, 'and `g` or "h"'), (4, 'from "A'), (5, 'B" on')])]
	[1, 4]
	"""
	open_spans: set[str] = set()
	for number, text in lines:
		text = text.replace("```", "")
		for delimiter in SPAN_DELIMITERS:
			odd: bool = text.count(delimiter) % 2 == 1
			text = text.replace(delimiter, "")
			if odd and delimiter not in open_spans:
				yield Violation(number, "split-span", f"{delimiter}...{delimiter} split across lines, keep it on one line")
			if odd:
				open_spans ^= {delimiter}


def code_block_indent(content: str, indent: int) -> int | None:
	""" Indent that lines must exceed to belong to the code a docstring line opens, None when it opens none.

	A doctest owns the lines at its own indent until a blank line, an RST block only the deeper ones.
	"""
	if content.startswith(">>>"):
		return indent - 1
	if content.endswith("::") or content.startswith(".. code"):
		return indent
	return None


def strands_fragment(previous: str, current: str, max_words: int) -> bool:
	""" Whether a line break cuts a clause and leaves at most ``max_words`` of its words alone on one side.

	A break after a comma or a semicolon falls between clauses, which reads fine.

	>>> strands_fragment("The wrapper is generic, so they come", "from :py:mod:`cli`. Only the rest is ours.", 3)
	True
	>>> strands_fragment("The wrapper is generic,", "so they come from :py:mod:`cli`.", 3)
	False
	>>> strands_fragment("Roll once per tick. The", "caller resets the counter.", 3)
	True
	>>> strands_fragment("Args:", "limit: Retries", 3)
	False
	"""
	if not current[:1].islower() or previous.endswith(CLAUSE_ENDINGS) or "=" in previous + current or NEW_ITEM.match(current):
		return False
	tail: list[str] = CLAUSE_BOUNDARY.split(previous)[-1].split()
	head: list[str] = CLAUSE_BOUNDARY.split(current)[0].split()
	return min(len(tail), len(head)) <= max_words

