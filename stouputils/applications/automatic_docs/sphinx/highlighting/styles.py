""" Pygments transcriptions of the two default VS Code themes, Dark+ and Light+.

The colours are the ones the editor ships, so a snippet in the documentation matches the same snippet in the reader's
editor: types teal, functions yellow, variables light blue, strings orange, control flow purple.
They only pay off together with :class:`.VSCodeSemanticFilter`, which is what tells a call apart from a variable.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"pygments.style",
	"pygments.token",
})

# Imports
from pygments.style import Style
from pygments.token import (
	Comment,
	Error,
	Generic,
	Keyword,
	Name,
	Number,
	Operator,
	Punctuation,
	String,
	Text,
	Token,
	Whitespace,
)


# Classes
class VSCodeDarkPlusStyle(Style):
	""" The VS Code "Dark Modern" / Dark+ palette. """

	name = "vscode-dark-plus"
	background_color = "#1F1F1F"
	highlight_color = "#264F78"
	line_number_color = "#6E7681"
	line_number_background_color = "#1F1F1F"

	styles = {  # noqa: RUF012
		Token:                 "#D4D4D4",
		Text:                  "#D4D4D4",
		Whitespace:            "#D4D4D4",
		Error:                 "#F14C4C",

		Comment:               "italic #6A9955",
		Comment.Preproc:       "#569CD6",

		Keyword:               "#C586C0",
		Keyword.Constant:      "#569CD6",
		Keyword.Declaration:   "#569CD6",
		Keyword.Namespace:     "#C586C0",
		Keyword.Type:          "#4EC9B0",

		Name:                  "#9CDCFE",
		Name.Attribute:        "#9CDCFE",
		Name.Builtin:          "#DCDCAA",
		Name.Builtin.Pseudo:   "#9CDCFE",
		Name.Class:            "#4EC9B0",
		Name.Constant:         "#9CDCFE",
		Name.Decorator:        "#DCDCAA",
		Name.Entity:           "#9CDCFE",
		Name.Exception:        "#4EC9B0",
		Name.Function:         "#DCDCAA",
		Name.Function.Magic:   "#DCDCAA",
		Name.Label:            "#C8C8C8",
		Name.Namespace:        "#4EC9B0",
		Name.Tag:              "#569CD6",
		Name.Variable:         "#9CDCFE",
		Name.Variable.Magic:   "#9CDCFE",

		String:                "#CE9178",
		String.Affix:          "#569CD6",
		String.Doc:            "#CE9178",
		String.Escape:         "#D7BA7D",
		String.Interpol:       "#569CD6",
		String.Regex:          "#D16969",

		Number:                "#B5CEA8",
		Operator:              "#D4D4D4",
		Operator.Word:         "#569CD6",
		Punctuation:           "#D4D4D4",

		Generic.Deleted:       "#F14C4C",
		Generic.Emph:          "italic",
		Generic.Error:         "#F14C4C",
		Generic.Heading:       "bold #569CD6",
		Generic.Inserted:      "#6A9955",
		Generic.Output:        "#CCCCCC",
		Generic.Prompt:        "#6E7681",
		Generic.Strong:        "bold",
		Generic.Subheading:    "bold #569CD6",
		Generic.Traceback:     "#F14C4C",
	}


class VSCodeLightPlusStyle(Style):
	""" The VS Code "Light Modern" / Light+ palette, mapped token for token onto its dark sibling. """

	name = "vscode-light-plus"
	background_color = "#FFFFFF"
	highlight_color = "#ADD6FF"
	line_number_color = "#6E7681"
	line_number_background_color = "#FFFFFF"

	styles = {  # noqa: RUF012
		Token:                 "#000000",
		Text:                  "#000000",
		Whitespace:            "#000000",
		Error:                 "#CD3131",

		Comment:               "italic #008000",
		Comment.Preproc:       "#0000FF",

		Keyword:               "#AF00DB",
		Keyword.Constant:      "#0000FF",
		Keyword.Declaration:   "#0000FF",
		Keyword.Namespace:     "#AF00DB",
		Keyword.Type:          "#267F99",

		Name:                  "#001080",
		Name.Attribute:        "#001080",
		Name.Builtin:          "#795E26",
		Name.Builtin.Pseudo:   "#001080",
		Name.Class:            "#267F99",
		Name.Constant:         "#001080",
		Name.Decorator:        "#795E26",
		Name.Entity:           "#001080",
		Name.Exception:        "#267F99",
		Name.Function:         "#795E26",
		Name.Function.Magic:   "#795E26",
		Name.Label:            "#3B3B3B",
		Name.Namespace:        "#267F99",
		Name.Tag:              "#800000",
		Name.Variable:         "#001080",
		Name.Variable.Magic:   "#001080",

		String:                "#A31515",
		String.Affix:          "#0000FF",
		String.Doc:            "#A31515",
		String.Escape:         "#EE0000",
		String.Interpol:       "#0000FF",
		String.Regex:          "#811F3F",

		Number:                "#098658",
		Operator:              "#000000",
		Operator.Word:         "#0000FF",
		Punctuation:           "#000000",

		Generic.Deleted:       "#CD3131",
		Generic.Emph:          "italic",
		Generic.Error:         "#CD3131",
		Generic.Heading:       "bold #0000FF",
		Generic.Inserted:      "#008000",
		Generic.Output:        "#3B3B3B",
		Generic.Prompt:        "#6E7681",
		Generic.Strong:        "bold",
		Generic.Subheading:    "bold #0000FF",
		Generic.Traceback:     "#CD3131",
	}

