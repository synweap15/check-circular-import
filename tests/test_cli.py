"""Tests for the CLI interface."""

import json
import subprocess
import sys
from pathlib import Path


def test_cli_help():
    """Test that --help works."""
    result = subprocess.run(
        [sys.executable, "-m", "check_circular_import", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Detect circular imports" in result.stdout
    assert "--json" in result.stdout
    assert "--ignore" in result.stdout


def test_cli_version():
    """Test that --version works and matches package version."""
    from check_circular_import import __version__

    result = subprocess.run(
        [sys.executable, "-m", "check_circular_import", "--version"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert __version__ in result.stdout


def test_cli_with_circular_imports(project_with_circular_imports: Path):
    """Test CLI with a project containing circular imports."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "check_circular_import",
            str(project_with_circular_imports),
        ],
        capture_output=True,
        text=True,
    )

    # Should exit with code 1 when cycles are found
    assert result.returncode == 1
    assert "circular import" in result.stdout.lower()
    assert "module_a" in result.stdout
    assert "module_b" in result.stdout


def test_cli_with_clean_project(clean_project: Path):
    """Test CLI with a clean project."""
    result = subprocess.run(
        [sys.executable, "-m", "check_circular_import", str(clean_project)],
        capture_output=True,
        text=True,
    )

    # Should exit with code 0 when no cycles are found
    assert result.returncode == 0
    assert "No circular imports detected" in result.stdout


def test_cli_json_output(project_with_circular_imports: Path):
    """Test CLI JSON output format."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "check_circular_import",
            str(project_with_circular_imports),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Should still exit with code 1
    assert result.returncode == 1

    # Parse JSON output
    data = json.loads(result.stdout)
    assert "root_directory" in data
    assert "statistics" in data
    assert "cycles" in data
    assert len(data["cycles"]) > 0


def test_cli_ignore_directories(temp_project_dir: Path):
    """Test CLI --ignore option."""
    # Create a module in a directory that should be ignored
    ignored_dir = temp_project_dir / "ignored"
    ignored_dir.mkdir()
    (ignored_dir / "module.py").write_text("import sys")

    # Create a regular module
    (temp_project_dir / "regular.py").write_text("import os")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "check_circular_import",
            str(temp_project_dir),
            "--ignore",
            "ignored",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # The ignored directory should not be analyzed
    assert "ignored" not in result.stdout


def test_cli_verbose_mode(clean_project: Path):
    """Test CLI verbose mode."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "check_circular_import",
            str(clean_project),
            "--verbose",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Analyzing Python files in:" in result.stdout
    assert "Ignoring directories:" in result.stdout


def test_cli_current_directory():
    """Test CLI with current directory (default)."""
    result = subprocess.run(
        [sys.executable, "-m", "check_circular_import"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),  # Run from project root
    )

    # Should complete without crashing
    assert result.returncode in [0, 1]
    assert "CIRCULAR IMPORT DETECTION REPORT" in result.stdout


def test_cli_nonexistent_directory():
    """Test CLI with non-existent directory."""
    result = subprocess.run(
        [sys.executable, "-m", "check_circular_import", "/nonexistent/path"],
        capture_output=True,
        text=True,
    )

    # Should handle gracefully
    assert result.returncode == 0
    assert "Total modules analyzed: 0" in result.stdout
