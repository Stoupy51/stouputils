""" Common functions used by the Linux and Windows installers modules. """
# Imports
from typing import Literal

from ..print import warning


# Functions
def prompt_for_path(prompt_message: str, default_path: str) -> str:
	""" Prompt the user to override a default path.

	Args:
		prompt_message (str): The message to display to the user.
		default_path   (str): The default path to suggest.

	Returns:
		str: The path entered by the user, or the default path if they pressed Enter.
	"""
	warning(f"{prompt_message}\nPress Enter to use this path, or type a new path to override it: ")
	return input() or default_path


def ask_install_type(ask_global: int, default_local_path: str, default_global_path: str | None) -> Literal["g", "l"]:
	""" Determine the installation type (global 'g' or local 'l') based on user input.

	Args:
		ask_global          (int):           0 = ask, 1 = force global, 2 = force local.
		default_local_path  (str):           The default local path.
		default_global_path (str | None):    The default global path (if applicable).

	Returns:
		Literal["g", "l"]: 'g' for global install, 'l' for local install.

	Examples:
		.. code-block:: python

			> # Ask the user while providing default paths
			> install_choice: str = ask_install_type(0, f"{os.getcwd()}/MyProgram", "C:\\Program Files\\MyProgram")
			g

			> # Don't ask, force global
			> install_choice: str = ask_install_type(1, ...)
			g

			> # Don't ask, force local
			> install_choice: str = ask_install_type(2, ...)
			l
	"""
	install_choice: str = ""
	if ask_global == 0:
		if default_global_path:
			global_prompt: str = f"(Globally would target '{default_global_path}')"
		else:
			global_prompt: str = "(Global install not well-defined)"
		warning(
			f"Install globally (requires admin/sudo, suggests adding to PATH) or locally? (G/l):\n"
			f"{global_prompt}, locally would be '{default_local_path}')"
		)
		install_choice = input().lower()
	elif ask_global == 1:
		install_choice = "g"
	elif ask_global == 2:
		install_choice = "l"

	# Default to global unless user explicitly chooses local ('l')
	return 'l' if install_choice == 'l' else 'g'

