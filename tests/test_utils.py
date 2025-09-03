"""Test utilities and helper functions."""

from pathlib import Path

from check_circular_import.detector import CircularImportDetector


def create_module_files(base_dir: Path, modules: dict[str, str]) -> None:
    """
    Create multiple Python module files from a dictionary.

    Args:
        base_dir: Base directory to create files in
        modules: Dict mapping module names to their content
    """
    for module_name, content in modules.items():
        if "/" in module_name:
            # Handle nested modules
            parts = module_name.split("/")
            module_path = base_dir
            for part in parts[:-1]:
                module_path = module_path / part
                module_path.mkdir(exist_ok=True)
                # Create __init__.py for packages
                (module_path / "__init__.py").touch()

            file_path = module_path / f"{parts[-1]}.py"
        else:
            file_path = base_dir / f"{module_name}.py"

        file_path.write_text(content.strip())


def analyze_project(project_dir: Path) -> tuple[list[list[str]], dict]:
    """
    Analyze a project directory and return cycles and stats.

    Args:
        project_dir: Directory to analyze

    Returns:
        Tuple of (cycles, stats)
    """
    detector = CircularImportDetector(str(project_dir))
    return detector.analyze()


def assert_cycles_contain_modules(
    cycles: list[list[str]], expected_modules: list[str]
) -> None:
    """
    Assert that the detected cycles contain all expected modules.

    Args:
        cycles: List of detected cycles
        expected_modules: List of module names that should be in cycles
    """
    all_cycle_modules = set()
    for cycle in cycles:
        all_cycle_modules.update(cycle)

    for module in expected_modules:
        assert any(
            module in cycle_module for cycle_module in all_cycle_modules
        ), f"Expected module '{module}' not found in cycles: {all_cycle_modules}"


def assert_no_cycles(cycles: list[list[str]]) -> None:
    """Assert that no cycles were detected."""
    assert len(cycles) == 0, f"Expected no cycles, but found: {cycles}"


def create_chain_modules(base_dir: Path, chain: list[str]) -> None:
    """
    Create modules that import in a chain (A -> B -> C -> ... -> A).

    Args:
        base_dir: Directory to create modules in
        chain: List of module names forming the chain
    """
    modules = {}

    for i, module in enumerate(chain):
        next_module = chain[(i + 1) % len(chain)]
        modules[
            module
        ] = f"""
import {next_module}

def func_{module}():
    return {next_module}.func_{next_module}()
"""

    create_module_files(base_dir, modules)


def create_package_structure(
    base_dir: Path, package_name: str, submodules: dict[str, str]
) -> None:
    """
    Create a package with submodules.

    Args:
        base_dir: Base directory
        package_name: Name of the package
        submodules: Dict of submodule names to their import statements
    """
    pkg_dir = base_dir / package_name
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    modules = {}
    for submodule, imports in submodules.items():
        modules[
            f"{package_name}/{submodule}"
        ] = f"""
{imports}

def func_{submodule}():
    return "result from {submodule}"
"""

    create_module_files(base_dir, modules)
