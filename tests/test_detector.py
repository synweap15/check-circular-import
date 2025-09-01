"""Tests for the CircularImportDetector class."""

from pathlib import Path

from check_circular_import.detector import CircularImportDetector


def test_detector_finds_simple_circular_import(project_with_circular_imports: Path):
    """Test that detector finds a simple circular import between two modules."""
    detector = CircularImportDetector(str(project_with_circular_imports))
    cycles, stats = detector.analyze()

    assert len(cycles) > 0
    assert stats["circular_dependencies_found"] > 0

    # Check that the cycle contains both modules
    cycle_modules = set()
    for cycle in cycles:
        cycle_modules.update(cycle)

    assert "module_a" in cycle_modules
    assert "module_b" in cycle_modules


def test_detector_finds_nested_circular_imports(
    project_with_nested_circular_imports: Path,
):
    """Test that detector finds circular imports in nested packages."""
    detector = CircularImportDetector(str(project_with_nested_circular_imports))
    cycles, stats = detector.analyze()

    assert len(cycles) > 0
    assert stats["circular_dependencies_found"] > 0

    # Check that the cycle contains all three submodules
    cycle_modules = set()
    for cycle in cycles:
        cycle_modules.update(cycle)

    assert any("submodule_a" in module for module in cycle_modules)
    assert any("submodule_b" in module for module in cycle_modules)
    assert any("submodule_c" in module for module in cycle_modules)


def test_detector_clean_project_no_cycles(clean_project: Path):
    """Test that detector correctly reports no cycles in a clean project."""
    detector = CircularImportDetector(str(clean_project))
    cycles, stats = detector.analyze()

    assert len(cycles) == 0
    assert stats["circular_dependencies_found"] == 0
    assert stats["total_modules"] == 3  # utils, main, app


def test_detector_handles_relative_imports(project_with_relative_imports: Path):
    """Test that detector correctly handles relative imports."""
    detector = CircularImportDetector(str(project_with_relative_imports))
    cycles, stats = detector.analyze()

    assert len(cycles) > 0

    # Check that relative imports are detected
    cycle_modules = set()
    for cycle in cycles:
        cycle_modules.update(cycle)

    assert any("models" in module for module in cycle_modules)
    assert any("views" in module for module in cycle_modules)


def test_detector_ignores_directories():
    """Test that detector correctly ignores specified directories."""
    detector = CircularImportDetector(".", ignore_dirs=["venv", "test_dir"])

    assert "venv" in detector.ignore_dirs
    assert "test_dir" in detector.ignore_dirs
    assert "__pycache__" in detector.ignore_dirs  # Default ignore


def test_detector_stats_accuracy(clean_project: Path):
    """Test that detector provides accurate statistics."""
    detector = CircularImportDetector(str(clean_project))
    cycles, stats = detector.analyze()

    assert stats["total_modules"] == 3
    assert stats["modules_with_dependencies"] == 2  # main and app have dependencies
    assert stats["total_dependencies"] >= 2  # main->utils, app->main, app->utils


def test_detector_handles_nonexistent_directory():
    """Test that detector handles non-existent directories gracefully."""
    detector = CircularImportDetector("/nonexistent/directory")
    cycles, stats = detector.analyze()

    assert len(cycles) == 0
    assert stats["total_modules"] == 0


def test_detector_handles_syntax_errors(temp_project_dir: Path):
    """Test that detector handles Python files with syntax errors."""
    # Create a file with syntax error
    bad_file = temp_project_dir / "bad_syntax.py"
    bad_file.write_text(
        """
    def bad_function(
        This is invalid Python syntax
    """
    )

    # Create a valid file
    good_file = temp_project_dir / "good.py"
    good_file.write_text(
        """
def good_function():
    return "OK"
"""
    )

    detector = CircularImportDetector(str(temp_project_dir))
    cycles, stats = detector.analyze()

    # Should still analyze the good file
    assert stats["total_modules"] >= 1


def test_detector_handles_complex_cycle(temp_project_dir: Path):
    """Test detection of a more complex circular dependency chain."""
    # Create a -> b -> c -> d -> a cycle
    modules = ["mod_a", "mod_b", "mod_c", "mod_d"]

    for i, mod in enumerate(modules):
        next_mod = modules[(i + 1) % len(modules)]
        file_path = temp_project_dir / f"{mod}.py"
        file_path.write_text(
            f"""
import {next_mod}

def func_{mod}():
    return {next_mod}.func_{next_mod}()
"""
        )

    detector = CircularImportDetector(str(temp_project_dir))
    cycles, stats = detector.analyze()

    assert len(cycles) > 0
    assert stats["circular_dependencies_found"] > 0

    # All modules should be in the cycle
    cycle_modules = set()
    for cycle in cycles:
        cycle_modules.update(cycle)

    for mod in modules:
        assert mod in cycle_modules
