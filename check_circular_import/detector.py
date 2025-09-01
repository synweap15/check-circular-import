"""Core circular import detection logic."""

import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from check_circular_import.utils import (
    file_to_module_name,
    get_python_files,
    normalize_cycle,
)


class CircularImportDetector:
    """Detector for circular import dependencies in Python projects."""

    def __init__(self, root_directory: str, ignore_dirs: Optional[List[str]] = None):
        """
        Initialize the detector with a root directory to scan.

        Args:
            root_directory: The root directory of the project to analyze
            ignore_dirs: List of directory names to ignore
        """
        self.root_directory = Path(root_directory).resolve()
        default_ignore_dirs = [
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

        if ignore_dirs is None:
            self.ignore_dirs = default_ignore_dirs
        else:
            # Combine default and custom ignore directories
            self.ignore_dirs = list(set(default_ignore_dirs + ignore_dirs))
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.module_to_file: Dict[str, Path] = {}

    def extract_imports(self, file_path: Path) -> Set[str]:
        """Extract all imports from a Python file."""
        imports = set()

        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        # This is a relative import
                        current_module = file_to_module_name(
                            file_path, self.root_directory
                        )
                        current_parts = current_module.split(".")

                        if node.level <= len(current_parts):
                            base_parts = (
                                current_parts[: -node.level]
                                if node.level < len(current_parts)
                                else []
                            )
                            if node.module:
                                full_module = ".".join(base_parts + [node.module])
                            else:
                                full_module = ".".join(base_parts)
                            imports.add(full_module)

                            # Also add specific imports from relative imports
                            for alias in node.names:
                                if alias.name != "*":
                                    specific_module = ".".join(
                                        base_parts + [alias.name]
                                    )
                                    imports.add(specific_module)
                    elif node.module:
                        # Absolute import
                        imports.add(node.module)

                        # For "from X import Y", also consider X.Y as a potential module
                        for alias in node.names:
                            if alias.name != "*":
                                potential_module = f"{node.module}.{alias.name}"
                                imports.add(potential_module)

        except (SyntaxError, FileNotFoundError) as e:
            print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)

        return imports

    def build_dependency_graph(self) -> None:
        """Build the dependency graph from all Python files."""
        python_files = get_python_files(self.root_directory, self.ignore_dirs)

        # First pass: map all modules to their files
        for file_path in python_files:
            module_name = file_to_module_name(file_path, self.root_directory)
            self.module_to_file[module_name] = file_path

        # Second pass: build dependency graph
        for file_path in python_files:
            module_name = file_to_module_name(file_path, self.root_directory)
            imports = self.extract_imports(file_path)

            for imported_module in imports:
                # Only track internal project imports
                if self.is_internal_import(imported_module):
                    self.dependency_graph[module_name].add(imported_module)

    def is_internal_import(self, module_name: str) -> bool:
        """Check if an import is internal to the project."""
        # Check if the module or any parent module exists in our project
        parts = module_name.split(".")

        for i in range(len(parts), 0, -1):
            potential_module = ".".join(parts[:i])
            if potential_module in self.module_to_file:
                return True

        return False

    def find_cycles(self) -> List[List[str]]:
        """Find all cycles in the dependency graph using DFS."""
        cycles = []
        visited = set()
        rec_stack: List[str] = []

        def dfs(module: str) -> None:
            if module in rec_stack:
                # Found a cycle
                cycle_start = rec_stack.index(module)
                cycle = rec_stack[cycle_start:] + [module]
                cycles.append(cycle)
                return

            if module in visited:
                return

            visited.add(module)
            rec_stack.append(module)

            for neighbor in self.dependency_graph.get(module, []):
                dfs(neighbor)

            rec_stack.pop()

        # Start DFS from each unvisited node
        for module in self.dependency_graph:
            if module not in visited:
                dfs(module)

        # Remove duplicate cycles
        unique_cycles = []
        seen = set()

        for cycle in cycles:
            normalized = normalize_cycle(cycle)
            if normalized not in seen:
                seen.add(normalized)
                unique_cycles.append(list(normalized))

        return unique_cycles

    def analyze(self) -> Tuple[List[List[str]], Dict]:
        """
        Perform the full analysis.

        Returns:
            A tuple of (cycles, stats) where cycles is a list of circular dependencies
            and stats is a dictionary with analysis statistics.
        """
        self.build_dependency_graph()
        cycles = self.find_cycles()

        stats = {
            "total_modules": len(self.module_to_file),
            "total_dependencies": sum(
                len(deps) for deps in self.dependency_graph.values()
            ),
            "modules_with_dependencies": len(self.dependency_graph),
            "circular_dependencies_found": len(cycles),
        }

        return cycles, stats
