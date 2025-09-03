"""Additional complex tests to raise coverage and exercise edge branches."""

from pathlib import Path
from typing import Set

from check_circular_import.detector import CircularImportDetector
from check_circular_import.utils import (
    file_to_module_name,
    normalize_cycle,
)


def test_regex_fallback_parses_imports_when_ast_fails(
    temp_project_dir: Path,
) -> None:
    """Ensure regex fallback handles both import and from-import
    syntax when AST fails.
    """
    # Create a file with invalid syntax to force AST failure, with realistic lines
    bad = temp_project_dir / "bad.py"
    bad.write_text(
        """
??? this is not valid python ???
import pkg.mod
from pkg.mod import a, b as bee, *
"""
    )

    # Create a minimal package structure so the detector recognizes internal imports
    (temp_project_dir / "pkg").mkdir()
    (temp_project_dir / "pkg" / "__init__.py").write_text("")
    (temp_project_dir / "pkg" / "mod.py").write_text("# module")

    det = CircularImportDetector(str(temp_project_dir))
    # Call extract_imports directly to verify fallback parsing
    imports: Set[str] = det.extract_imports(bad)

    assert "pkg.mod" in imports
    # Should include specific names from from-import (excluding '*')
    assert "pkg.mod.a" in imports
    assert "pkg.mod.b" in imports
    # Star import should not produce a specific name entry
    assert not any(s.endswith(".*") for s in imports)


def test_fallback_read_text_failure(monkeypatch, temp_project_dir: Path) -> None:
    """If reading text fails during fallback, extractor returns safely (empty set)."""
    bad = temp_project_dir / "bad2.py"
    bad.write_text("not valid python")

    det = CircularImportDetector(str(temp_project_dir))

    # Monkeypatch Path.read_text to raise for this file
    original_read_text = Path.read_text

    def boom(self, *args, **kwargs):  # type: ignore[override]
        if self == bad:
            raise RuntimeError("boom")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", boom)

    imports = det.extract_imports(bad)
    assert imports == set()


def test_skip_root_init_in_graph(temp_project_dir: Path) -> None:
    """Root-level __init__.py should be ignored (no empty module name in graph)."""
    # Root-level __init__.py (ignored) and a regular module
    (temp_project_dir / "__init__.py").write_text("")
    (temp_project_dir / "a.py").write_text("# no imports")

    det = CircularImportDetector(str(temp_project_dir))
    cycles, stats = det.analyze()

    assert cycles == []
    # Only "a" should be counted as a module, not the root __init__.py
    assert stats["total_modules"] == 1


def test_file_to_module_name_nonrelative_returns_path(temp_project_dir: Path) -> None:
    """file_to_module_name returns raw path string when root is not a parent of file."""
    a = temp_project_dir / "a.py"
    a.write_text("# x")
    # Use a root directory that is not a parent
    other_root = temp_project_dir / "nested"
    other_root.mkdir()

    mod = file_to_module_name(a, other_root)
    assert mod == str(a)


def test_normalize_cycle_single_and_rotation() -> None:
    """Normalize handles single-item cycles and de-duplicates trailing element."""
    # Single element
    assert normalize_cycle(["only"]) == ("only",)

    # De-duplicate last element, rotate to smallest lexicographic start
    assert normalize_cycle(["b", "c", "a", "b"]) == ("a", "b", "c")
