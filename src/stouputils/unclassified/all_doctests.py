
# Imports
import os
import sys
ROOT_DIR: str = os.path.abspath(os.path.join(__file__, "..", ".."))
sys.path.insert(0, ROOT_DIR)
import src.iacob.config as conf
conf.ERROR_LOG = 100    # Set error log to 100 to raise all errors
from src.iacob.print import *
from doctest import TestResults, testmod
from types import ModuleType
import importlib
import pkgutil

def test_module_with_progress(module: ModuleType, separator: str) -> TestResults:
    """ Tests a module and displays execution time. """
    @measure_time(progress, message=f"Testing module '{module.__name__}' {separator}took")
    def internal() -> TestResults:
        return testmod(m=module)
    return internal()

# Main program
if __name__ == "__main__":

    # Get all modules from src package
    modules_file_paths: list[str] = []
    for directory_path, _, _ in os.walk(os.path.join(ROOT_DIR, "src")):
        for module_info in pkgutil.walk_packages([directory_path]):
            absolute_module_path: str = os.path.join(directory_path, module_info.name)
            path: str = absolute_module_path.replace(ROOT_DIR, "").replace(os.sep, ".")[1:]
            modules_file_paths.append(path)

    # Find longest module path for alignment
    max_length: int = max(len(path) for path in modules_file_paths)

    # Dynamically import all modules from iacob package recursively using pkgutil and importlib
    modules: list[ModuleType] = []
    separators: list[str] = []
    for module_path in modules_file_paths:
        try:
            separator: str = " " * (max_length - len(module_path))
            @measure_time(progress, message=f"Importing module '{module_path}' {separator}took")
            def internal() -> ModuleType:
                return importlib.import_module(module_path)
            modules.append(internal())
            separators.append(separator)
        except ImportError:
            warning(f"Unable to import module {module_path}")

    # Run tests for each module
    separators = [s + " "*(len("Importing") - len("Testing")) for s in separators]
    results: list[TestResults] = [test_module_with_progress(module, separator) for module, separator in zip(modules, separators)]

    # Display any error lines for each module at the end of the script
    for module, result in zip(modules, results):
        if result.failed > 0:
            error(f"Errors in module {module.__name__}", exit=False)

