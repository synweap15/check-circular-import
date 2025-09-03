"""Tests for edge cases and special scenarios."""

from pathlib import Path

from tests.test_utils import (
    analyze_project,
    assert_cycles_contain_modules,
    assert_no_cycles,
    create_module_files,
)


def test_self_import_detection(temp_project_dir: Path):
    """Test detection of modules that import themselves."""
    modules = {
        "self_import": """
import self_import

def recursive_func():
    return self_import.recursive_func()
""",
        "normal_module": """
def normal_func():
    return "normal"
""",
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Self-imports should be detected as cycles
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["self_import"])


def test_try_except_imports(temp_project_dir: Path):
    """Test handling of imports inside try/except blocks."""
    modules = {
        "try_a": """
try:
    import try_b
except ImportError:
    import fallback_module
""",
        "try_b": """
try:
    from try_a import something
except ImportError:
    pass
""",
        "fallback_module": """
def fallback():
    return "fallback"
""",
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Should detect cycles even in try/except
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["try_a", "try_b"])


def test_dynamic_imports(temp_project_dir: Path):
    """Test that dynamic imports (importlib) are not detected."""
    modules = {
        "dynamic_a": """
import importlib
import dynamic_b

# Dynamic import - should not be detected as circular
def load_module():
    return importlib.import_module('dynamic_c')
""",
        "dynamic_b": """
import dynamic_a

def use_a():
    return dynamic_a.load_module()
""",
        "dynamic_c": """
# This would create a cycle if detected dynamically, but shouldn't be
import dynamic_a
""",
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Should only detect the static cycle between dynamic_a and dynamic_b
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["dynamic_a", "dynamic_b"])


def test_future_imports(temp_project_dir: Path):
    """Test handling of __future__ imports."""
    modules = {
        "future_a": """
from __future__ import annotations
import future_b

def func_a() -> 'future_b.SomeType':
    return future_b.create_type()
""",
        "future_b": """
from __future__ import print_function
import future_a

def create_type():
    return future_a.func_a()
""",
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Should detect cycles despite __future__ imports
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["future_a", "future_b"])


def test_import_with_dots_and_underscores(temp_project_dir: Path):
    """Test modules with dots and underscores in names."""
    modules = {
        "module_with_underscore": """
import another.module.with.dots
""",
        "another/module/with/dots": """
import module_with_underscore
""",
        "another/__init__": "",
        "another/module/__init__": "",
        "another/module/with/__init__": "",
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    assert len(cycles) >= 1
    cycle_modules = set()
    for cycle in cycles:
        cycle_modules.update(cycle)

    # Should handle module names correctly
    assert any("module_with_underscore" in module for module in cycle_modules)
    assert any("another.module.with.dots" in module for module in cycle_modules)


def test_empty_files(temp_project_dir: Path):
    """Test handling of empty Python files."""
    modules = {
        "empty_a": "",
        "empty_b": "",
        "imports_empty": """
import empty_a
import empty_b
""",
        "normal": """
def func():
    return "normal"
""",
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Empty files shouldn't create cycles
    assert_no_cycles(cycles)
    assert stats["total_modules"] == 4


def test_very_long_import_chains(temp_project_dir: Path):
    """Test handling of very long import chains."""
    # Create a chain of 20 modules
    chain = [f"chain_{i:02d}" for i in range(20)]

    modules = {}
    for i, module in enumerate(chain):
        next_module = chain[(i + 1) % len(chain)]
        modules[module] = f"import {next_module}"

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Should detect the long cycle
    assert len(cycles) >= 1
    assert stats["circular_dependencies_found"] >= 1

    # All modules should be in some cycle
    cycle_modules = set()
    for cycle in cycles:
        cycle_modules.update(cycle)

    assert len(cycle_modules) >= 20


def test_import_error_handling(temp_project_dir: Path):
    """Test that import errors don't crash the analyzer."""
    modules = {
        "has_import_error": """
import nonexistent_module_xyz
import working_module
""",
        "working_module": """
import has_import_error

def work():
    return "working"
""",
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Should still detect cycles despite import errors
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["has_import_error", "working_module"])


def test_unicode_and_special_characters(temp_project_dir: Path):
    """Test handling of modules with Unicode content."""
    modules = {
        "unicode_module": """
# -*- coding: utf-8 -*-
import other_module

def función():
    return "Ñoño español"
""",
        "other_module": """
import unicode_module

def function():
    return unicode_module.función()
""",
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Should handle Unicode without issues
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["unicode_module", "other_module"])


def test_docstring_imports(temp_project_dir: Path):
    """Test that imports in docstrings are not detected."""
    modules = {
        "docstring_a": '''
"""
This module imports docstring_b.
Example:
    import docstring_b
    docstring_b.func()
"""
import docstring_b  # This should be detected

def func_a():
    return docstring_b.func_b()
''',
        "docstring_b": '''
"""
import docstring_a  # This should NOT be detected
"""
import docstring_a  # This should be detected

def func_b():
    return "b"
''',
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Should detect the actual imports, not the ones in docstrings
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["docstring_a", "docstring_b"])


def test_commented_imports(temp_project_dir: Path):
    """Test that commented-out imports are not detected."""
    modules = {
        "comment_a": """
# import comment_b  # This should NOT be detected
import comment_b  # This should be detected

def func_a():
    return comment_b.func_b()
""",
        "comment_b": """
import comment_a  # Real import

def func_b():
    # import some_other_module  # Commented import
    return comment_a.func_a()
""",
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Should detect only the real imports
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["comment_a", "comment_b"])


def test_multiline_imports(temp_project_dir: Path):
    """Test handling of multiline import statements."""
    modules = {
        "multi_a": """
from multi_b import (
    function_one,
    function_two,
    function_three
)

def use_multi_b():
    return function_one() + function_two()
""",
        "multi_b": """
from multi_a import use_multi_b

def function_one():
    return "one"

def function_two():
    return "two"

def function_three():
    return use_multi_b()
""",
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Should detect cycles with multiline imports
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["multi_a", "multi_b"])


def test_import_as_with_cycles(temp_project_dir: Path):
    """Test import as statements in circular dependencies."""
    modules = {
        "alias_x": """
import alias_y as y_module
from alias_z import func as z_func

def x_func():
    return y_module.y_func() + z_func()
""",
        "alias_y": """
import alias_x as x_module

def y_func():
    return x_module.x_func()
""",
        "alias_z": """
import alias_x as x_mod

def func():
    return x_mod.x_func()
""",
    }

    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Should detect cycles despite aliases
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["alias_x", "alias_y", "alias_z"])
