""" Installer module for Linux/macOS specific functions.

Provides Linux/macOS specific implementations for checking admin privileges,
determining appropriate installation paths (global/local), and suggesting
how to add directories to the system's PATH environment variable.
"""
# Imports
import os

from ..decorators import LogLevels, handle_error
from ..io import clean_path
from ..print import debug, info, warning
from .common import ask_install_type, prompt_for_path


# Functions
@handle_error(message="Failed to suggest how to add to PATH (Linux)", error_log=LogLevels.WARNING_TRACEBACK)
def add_to_path_linux(install_path: str) -> bool:
	""" Suggest how to add install_path to PATH on Linux.

	Checks the current shell and provides instructions for adding the path
	to the appropriate configuration file (e.g., .bashrc, .zshrc, config.fish).

	Args:
		install_path (str): The path to add to the PATH environment variable.

	Returns:
		bool: True if instructions were provided, False otherwise (e.g., unknown shell).
	"""
	shell_config_files: dict[str, str] = {
		"bash": "~/.bashrc",
		"zsh": "~/.zshrc",
		"fish": "~/.config/fish/config.fish"
	}
	current_shell: str = os.environ.get("SHELL", "").split('/')[-1]
	config_file: str | None = shell_config_files.get(current_shell)

	if config_file:
		export_cmd: str = ""
		if current_shell == "fish":
			export_cmd = f"set -gx PATH $PATH {install_path}"
		else:
			export_cmd = f"export PATH=\"$PATH:{install_path}\"" # Escape quotes for print

		debug(
			f"To add the installation directory to your PATH, add the following line to your '{config_file}':\n"
			f"  {export_cmd}\n"
			f"Then restart your shell or run 'source {config_file}'."
		)
		return True
	else:
		warning(f"Could not determine your shell configuration file. Please add '{install_path}' to your PATH manually.")
		return False


def check_admin_linux() -> bool:
	""" Check if the script is running with root privileges on Linux/macOS.

	Returns:
		bool: True if the effective user ID is 0 (root), False otherwise.
	"""
	try:
		return os.geteuid() == 0 # type: ignore
	except AttributeError as e:
		# os.geteuid() is not available on all platforms (e.g., Windows)
		# This function should ideally only be called on Linux/macOS.
		warning(f"Could not determine user privileges on this platform: {e}")
		return False
	except Exception as e:
		warning(f"Error checking admin privileges: {e}")
		return False


@handle_error(message="Failed to get installation path (Linux)", error_log=LogLevels.ERROR_TRACEBACK)
def get_install_path_linux(
	program_name: str,
	ask_global: int = 0,
	add_path: bool = True,
	append_to_path: str = "",
	default_global: str = "/usr/local/bin",
	) -> str:
	""" Get the installation path for the program on Linux/macOS.

	Args:
		program_name   (str):   The name of the program to install.
		ask_global     (int):   0 = ask for anything, 1 = install globally, 2 = install locally
		add_path       (bool):  Whether to add the program to the PATH environment variable. (Only if installed globally)
		append_to_path (str):   String to append to the installation path when adding to PATH.
			(ex: "bin" if executables are in the bin folder)
		default_global (str):   The default global installation path.
			(Default is "/usr/local/bin" which is the most common location for executables on Linux/macOS,
			could be "/opt" or any other directory)

	Returns:
		str: The chosen installation path, or an empty string if installation is cancelled.
	"""
	# Default paths
	default_local_path: str = clean_path(os.path.join(os.getcwd(), program_name))

	# Common global locations: /usr/local/bin for executables, /opt/ for self-contained apps
	# We assume 'program_name' might be an executable or a directory, /usr/local/ is safer
	default_global_path: str = clean_path(f"{default_global}/{program_name}") # Or potentially /opt/{program_name}

	# Ask user for installation type (global/local)
	install_type: str = ask_install_type(ask_global, default_local_path, default_global_path)

	# Handle global installation choice
	if install_type == 'g':
		if not check_admin_linux():
			warning(
				f"Global installation typically requires sudo privileges to write to "
				f"'{os.path.dirname(default_global_path)}'.\n"
				f"You may need to re-run the script with 'sudo'.\n"
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
		else:
			# User is admin or proceeding with global install anyway
			install_path: str = prompt_for_path(
				f"Default global installation path is {default_global_path}.",
				default_global_path
			)
			if add_path:
				# Suggest adding the *directory* containing the program to PATH,
				# or the path itself if it seems like a directory install
				path_to_add: str = os.path.dirname(install_path) if os.path.isfile(install_path) else install_path
				add_to_path_linux(os.path.join(path_to_add, append_to_path))
			return install_path

	# Handle local installation choice
	else: # install_type == 'l'
		return prompt_for_path(
			f"Default local installation path is {default_local_path}.",
			default_local_path
		)

