""" Style rules that ruff cannot express, checked on text files and Python sources.

Each rule of :data:`~rules.RULES` can be left out with ``ignore``, and the limits tuned, in ``pyproject.toml``:

.. code-block:: toml

	[tool.stouputils.check]
	ignore = ["tab-indentation", "space-alignment"]
	final-newlines = { ".py" = 1, ".json" = 1 }
	docstring-max-lines = 20
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .cli import (
	BANNED_CHARACTERS as BANNED_CHARACTERS,
	check_cli as check_cli,
	check_file as check_file,
	expand_paths as expand_paths,
)
from .python import (
	CLAUSE_BOUNDARY as CLAUSE_BOUNDARY,
	CLAUSE_ENDINGS as CLAUSE_ENDINGS,
	EXAMPLES_HEADER as EXAMPLES_HEADER,
	NEW_ITEM as NEW_ITEM,
	STRANDED_FRAGMENT as STRANDED_FRAGMENT,
	TYPED_ARGUMENT as TYPED_ARGUMENT,
	code_block_indent as code_block_indent,
	comment_errors as comment_errors,
	constant_errors as constant_errors,
	docstring_errors as docstring_errors,
	docstring_layout_errors as docstring_layout_errors,
	indentation_errors as indentation_errors,
	is_docstring as is_docstring,
	python_errors as python_errors,
	statements as statements,
	strands_fragment as strands_fragment,
	string_content_lines as string_content_lines,
)
from .rules import (
	RULES as RULES,
	CheckConfig as CheckConfig,
	Violation as Violation,
)

