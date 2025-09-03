"""Utility functions for circular import detection."""

import os
from fnmatch import fnmatch
from pathlib import Path

# Centralized default ignore patterns for directories
DEFAULT_IGNORE_DIRS: list[str] = [
    "venv",
    "env",
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    ".tox",
    "build",
    "dist",
    "*.egg-info",
]


def get_python_files(root_directory: Path, ignore_dirs: list[str]) -> list[Path]:
    """
    Find all Python files in the project directory.

    Args:
        root_directory: The root directory to search
        ignore_dirs: List of directory names to ignore

    Returns:
        List of Path objects for Python files
    """
    python_files = []

    for root, dirs, files in os.walk(root_directory):
        # Remove ignored directories from dirs to prevent walking into them
        # Support wildcard patterns like "*.egg-info"
        dirs[:] = [
            d for d in dirs if not any(fnmatch(d, pattern) for pattern in ignore_dirs)
        ]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    return python_files


def file_to_module_name(file_path: Path, root_directory: Path) -> str:
    """
    Convert a file path to a module name.

    Args:
        file_path: Path to the Python file
        root_directory: Root directory of the project

    Returns:
        Module name as a string
    """
    try:
        # Get relative path from root directory
        relative_path = file_path.relative_to(root_directory)

        # Remove .py extension and convert to module notation
        module_parts = relative_path.with_suffix("").parts

        # Handle __init__.py files
        if module_parts[-1] == "__init__":
            module_parts = module_parts[:-1]

        # If this is root-level __init__.py, ignore by returning empty name
        return ".".join(module_parts) if module_parts else ""
    except ValueError:
        return str(file_path)


def normalize_cycle(cycle: list[str]) -> tuple[str, ...]:
    """
    Normalize a cycle to start from the smallest element.

    Args:
        cycle: List of module names forming a cycle

    Returns:
        Normalized tuple of module names
    """
    if len(cycle) > 1:
        # Remove the duplicate last element if present
        if cycle[0] == cycle[-1]:
            cycle = cycle[:-1]

        # Find the minimum element and rotate
        min_idx = cycle.index(min(cycle))
        normalized = cycle[min_idx:] + cycle[:min_idx]
        return tuple(normalized)

    return tuple(cycle)


def format_cycle_output(cycle: list[str]) -> str:
    """
    Format a cycle for display.

    Args:
        cycle: List of module names forming a cycle

    Returns:
        Formatted string representation of the cycle
    """
    output_lines = []

    # Remove duplicate last element if it matches the first
    display_cycle = cycle[:-1] if cycle and cycle[0] == cycle[-1] else cycle

    for i, module in enumerate(display_cycle):
        output_lines.append(f"  {module}")
        if i < len(display_cycle) - 1:
            output_lines.append("    ↓ imports")

    # Add the cycle completion
    if display_cycle:
        output_lines.append("    ↓ imports")
        output_lines.append(f"  {display_cycle[0]} (cycle completes)")

    return "\n".join(output_lines)
