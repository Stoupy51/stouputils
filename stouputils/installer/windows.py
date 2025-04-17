""" Installer module for Windows specific functions.

Provides Windows specific implementations for checking administrator privileges,
determining appropriate installation paths (global/local), and modifying
the user's PATH environment variable.
"""
# Imports
import os

from ..decorators import LogLevels, handle_error
from ..io import clean_path
from ..print import debug, info, warning
from .common import ask_install_type, prompt_for_path


# Functions
@handle_error(message="Failed to add to PATH (Windows)", error_log=LogLevels.WARNING_TRACEBACK)
def add_to_path_windows(install_path: str) -> bool | None:
	""" Add install_path to the User PATH environment variable on Windows.

	Args:
		install_path (str): The path to add to the User PATH environment variable.

	Returns:
		bool | None: True if the path was added to the User PATH environment variable, None otherwise.
	"""
	# Convert install_path to a Windows path if it's not already
	install_path = install_path.replace("/", "\\")
	os.makedirs(install_path, exist_ok=True)

	# Get current user PATH
	import winreg
	with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:

		# Get the number of values in the registry key
		num_values = winreg.QueryInfoKey(key)[1]

		# Find the index of the 'Path' value
		path_index = -1
		for i in range(num_values):
			if winreg.EnumValue(key, i)[0] == 'Path':
				path_index = i
				break

		# Get the current path value
		current_path: str = winreg.EnumValue(key, path_index)[1]

		# Check if path is already present
		if install_path not in current_path.split(';'):
			new_path: str = f"{current_path};{install_path}"
			winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
			debug(f"Added '{install_path}' to user PATH. Please restart your terminal for changes to take effect.")
		else:
			debug(f"'{install_path}' is already in user PATH.")
	return True


def check_admin_windows() -> bool:
	""" Check if the script is running with administrator privileges on Windows. """
	try:
		import ctypes
		return ctypes.windll.shell32.IsUserAnAdmin() != 0
	except Exception:
		return False


@handle_error(message="Failed to get installation path (Windows)", error_log=LogLevels.ERROR_TRACEBACK)
def get_install_path_windows(
	program_name: str,
	ask_global: int = 0,
	add_path: bool = True,
	append_to_path: str = "",
	default_global: str = os.environ.get("ProgramFiles", "C:\\Program Files")
) -> str:
	""" Get the installation path for the program

	Args:
		program_name  (str):   The name of the program to install.
		ask_global    (int):   0 = ask for anything, 1 = install globally, 2 = install locally
		add_path      (bool):  Whether to add the program to the PATH environment variable. (Only if installed globally)
		append_to_path (str):  String to append to the installation path when adding to PATH.
			(ex: "bin" if executables are in the bin folder)
		default_global (str):  The default global installation path.
			(Default is "C:\\Program Files" which is the most common location for executables on Windows)

	Returns:
		str: The installation path.
	"""
	# Default path is located in the current working directory
	default_local_path: str = clean_path(os.path.join(os.getcwd(), program_name))

	# Define default global path (used in prompt even if not chosen initially)
	default_global_path: str = clean_path(os.path.join(default_global, program_name))

	# Ask user for installation type (global/local)
	install_type: str = ask_install_type(ask_global, default_local_path, default_global_path)

	# If the user wants to install globally,
	if install_type == 'g':

		# Check if the user has admin privileges,
		if not check_admin_windows():

			# If the user doesn't have admin privileges, fallback to local
			warning(
				f"Global installation requires administrator privileges. Please re-run as administrator.\n"
				f"Install locally instead to '{default_local_path}'? (Y/n): "
			)
			if input().lower() == 'n':
				info("Installation cancelled.")
				return ""
			else:
				# Fallback to local path if user agrees
				return prompt_for_path(
					f"Falling back to local installation path: {default_local_path}.",
					default_local_path
				)

		# If the user has admin privileges,
		else:
			# Ask it user wants to override the default global install path
			install_path: str = prompt_for_path(
				f"Default global installation path is {default_global_path}.",
				default_global_path
			)
			if add_path:
				add_to_path_windows(os.path.join(install_path, append_to_path))
			return install_path

	# Local install
	else: # install_type == 'l'
		return prompt_for_path(
			f"Default local installation path is {default_local_path}.",
			default_local_path
		)

