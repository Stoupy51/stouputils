
# Imports
import os
import sys
from .print import *
from .decorators import measure_time
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
def main(root_dir: str) -> None:
    sys.path.insert(0, root_dir)

    # Get all modules from src package
    modules_file_paths: list[str] = []
    for directory_path, _, _ in os.walk(root_dir):
        for module_info in pkgutil.walk_packages([directory_path]):
            absolute_module_path: str = os.path.join(directory_path, module_info.name)
            path: str = absolute_module_path.split(root_dir, 1)[1].replace(os.sep, ".")[1:]
            if path not in modules_file_paths:
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
    info(f"Testing {len(modules)} modules...")
    separators = [s + " "*(len("Importing") - len("Testing")) for s in separators]
    results: list[TestResults] = [test_module_with_progress(module, separator) for module, separator in zip(modules, separators)]

    # Display any error lines for each module at the end of the script
    for module, result in zip(modules, results):
        if result.failed > 0:
            error(f"Errors in module {module.__name__}", exit=False)

