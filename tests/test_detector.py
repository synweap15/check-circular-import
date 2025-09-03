"""Tests for the CircularImportDetector class."""

from pathlib import Path

from check_circular_import.detector import CircularImportDetector
from tests.test_utils import analyze_project, assert_cycles_contain_modules, assert_no_cycles


def test_detector_finds_simple_circular_import(project_with_circular_imports: Path):
    """Test that detector finds a simple circular import between two modules."""
    cycles, stats = analyze_project(project_with_circular_imports)

    assert len(cycles) > 0
    assert stats["circular_dependencies_found"] > 0
    assert_cycles_contain_modules(cycles, ["module_a", "module_b"])


def test_detector_finds_nested_circular_imports(
    project_with_nested_circular_imports: Path,
):
    """Test that detector finds circular imports in nested packages."""
    cycles, stats = analyze_project(project_with_nested_circular_imports)

    assert len(cycles) > 0
    assert stats["circular_dependencies_found"] > 0
    assert_cycles_contain_modules(cycles, ["submodule_a", "submodule_b", "submodule_c"])


def test_detector_clean_project_no_cycles(clean_project: Path):
    """Test that detector correctly reports no cycles in a clean project."""
    cycles, stats = analyze_project(clean_project)

    assert_no_cycles(cycles)
    assert stats["circular_dependencies_found"] == 0
    assert stats["total_modules"] == 3  # utils, main, app


def test_detector_handles_relative_imports(project_with_relative_imports: Path):
    """Test that detector correctly handles relative imports."""
    cycles, stats = analyze_project(project_with_relative_imports)

    assert len(cycles) > 0
    assert_cycles_contain_modules(cycles, ["models", "views"])


def test_detector_ignores_directories():
    """Test that detector correctly ignores specified directories."""
    detector = CircularImportDetector(".", ignore_dirs=["venv", "test_dir"])

    assert "venv" in detector.ignore_dirs
    assert "test_dir" in detector.ignore_dirs
    assert "__pycache__" in detector.ignore_dirs  # Default ignore


def test_detector_stats_accuracy(clean_project: Path):
    """Test that detector provides accurate statistics."""
    cycles, stats = analyze_project(clean_project)

    assert stats["total_modules"] == 3
    assert stats["modules_with_dependencies"] == 2  # main and app have dependencies
    assert stats["total_dependencies"] >= 2  # main->utils, app->main, app->utils


def test_detector_handles_nonexistent_directory():
    """Test that detector handles non-existent directories gracefully."""
    cycles, stats = analyze_project(Path("/nonexistent/directory"))

    assert_no_cycles(cycles)
    assert stats["total_modules"] == 0


def test_detector_handles_syntax_errors(temp_project_dir: Path):
    """Test that detector handles Python files with syntax errors."""
    from tests.test_utils import create_module_files
    
    modules = {
        "bad_syntax": """
def bad_function(
    This is invalid Python syntax
""",
        "good": """
def good_function():
    return "OK"
"""
    }
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)

    # Should still analyze the good file
    assert stats["total_modules"] >= 1


def test_detector_handles_complex_cycle(temp_project_dir: Path):
    """Test detection of a more complex circular dependency chain."""
    from tests.test_utils import create_chain_modules
    
    modules = ["mod_a", "mod_b", "mod_c", "mod_d"]
    create_chain_modules(temp_project_dir, modules)
    
    cycles, stats = analyze_project(temp_project_dir)

    assert len(cycles) > 0
    assert stats["circular_dependencies_found"] > 0
    assert_cycles_contain_modules(cycles, modules)
