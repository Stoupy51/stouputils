
# Imports
import json
import re
from typing import IO, Any

from .path import super_open


# JSON dump with indentation for levels
def json_dump(
	data: Any,
	file: IO[Any] | str | None = None,
	max_level: int | None = 2,
	indent: str | int = '\t',
	suffix: str = "\n",
	ensure_ascii: bool = False
) -> str:
	r""" Writes the provided data to a JSON file with a specified indentation depth.
	For instance, setting max_level to 2 will limit the indentation to 2 levels.

	Args:
		data		(Any): 				The data to dump (usually a dict or a list)
		file		(IO[Any] | str): 	The file object or path to dump the data to
		max_level	(int | None):		The depth of indentation to stop at (-1 for infinite), None will default to 2
		indent		(str | int):		The indentation character (default: '\t')
		suffix		(str):				The suffix to add at the end of the string (default: '\n')
		ensure_ascii (bool):			Whether to escape non-ASCII characters (default: False)
	Returns:
		str: The content of the file in every case

	>>> json_dump({"a": [[1,2,3]], "b": 2}, max_level = 0)
	'{"a": [[1,2,3]],"b": 2}\n'
	>>> json_dump({"a": [[1,2,3]], "b": 2}, max_level = 1)
	'{\n\t"a": [[1,2,3]],\n\t"b": 2\n}\n'
	>>> json_dump({"a": [[1,2,3]], "b": 2}, max_level = 2)
	'{\n\t"a": [\n\t\t[1,2,3]\n\t],\n\t"b": 2\n}\n'
	>>> json_dump({"a": [[1,2,3]], "b": 2}, max_level = 3)
	'{\n\t"a": [\n\t\t[\n\t\t\t1,\n\t\t\t2,\n\t\t\t3\n\t\t]\n\t],\n\t"b": 2\n}\n'
	>>> json_dump({"éà": "üñ"}, ensure_ascii = True, max_level = 0)
	'{"\\u00e9\\u00e0": "\\u00fc\\u00f1"}\n'
	>>> json_dump({"éà": "üñ"}, ensure_ascii = False, max_level = 0)
	'{"éà": "üñ"}\n'
	"""
	# Handle None values for max_level
	if max_level is None:
		max_level = 2

	# Dump content with 2-space indent and replace it with the desired indent
	content: str = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)

	# Limit max depth of indentation
	if max_level > -1:
		escape: str = re.escape(indent if isinstance(indent, str) else ' '*indent)
		pattern: re.Pattern[str] = re.compile(
			r"\n" + escape + "{" + str(max_level + 1) + r",}(.*)"
			r"|\n" + escape + "{" + str(max_level) + r"}([}\]])"
		)
		content = pattern.sub(r"\1\2", content)

	# Final newline and write
	content += suffix
	if file:
		if isinstance(file, str):
			with super_open(file, "w") as f:
				f.write(content)
		else:
			file.write(content)
	return content

# JSON load from file path
def json_load(file_path: str) -> Any:
	""" Load a JSON file from the given path

	Args:
		file_path (str): The path to the JSON file
	Returns:
		Any: The content of the JSON file
	"""
	with open(file_path) as f:
		return json.loads(f.read())

