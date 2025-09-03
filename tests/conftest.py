"""Pytest configuration and fixtures."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test projects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def project_with_circular_imports(temp_project_dir: Path) -> Path:
    """Create a test project with circular imports."""
    # Create module_a.py that imports module_b
    module_a = temp_project_dir / "module_a.py"
    module_a.write_text(
        """
import module_b

def func_a():
    return module_b.func_b()
"""
    )

    # Create module_b.py that imports module_a (circular!)
    module_b = temp_project_dir / "module_b.py"
    module_b.write_text(
        """
import module_a

def func_b():
    return "Hello from B"
"""
    )

    return temp_project_dir


@pytest.fixture
def project_with_nested_circular_imports(temp_project_dir: Path) -> Path:
    """Create a test project with nested circular imports."""
    # Create package structure
    pkg_dir = temp_project_dir / "mypackage"
    pkg_dir.mkdir()

    # Create __init__.py
    (pkg_dir / "__init__.py").write_text("")

    # Create submodule_a.py
    (pkg_dir / "submodule_a.py").write_text(
        """
from mypackage import submodule_b

def func_a():
    return submodule_b.func_b()
"""
    )

    # Create submodule_b.py
    (pkg_dir / "submodule_b.py").write_text(
        """
from mypackage import submodule_c

def func_b():
    return submodule_c.func_c()
"""
    )

    # Create submodule_c.py (completes the cycle)
    (pkg_dir / "submodule_c.py").write_text(
        """
from mypackage import submodule_a

def func_c():
    return "Hello from C"
"""
    )

    return temp_project_dir


@pytest.fixture
def clean_project(temp_project_dir: Path) -> Path:
    """Create a test project without circular imports."""
    # Create utils.py
    utils = temp_project_dir / "utils.py"
    utils.write_text(
        """
def helper():
    return "Helper function"
"""
    )

    # Create main.py that imports utils
    main = temp_project_dir / "main.py"
    main.write_text(
        """
import utils

def main():
    return utils.helper()
"""
    )

    # Create app.py that imports both
    app = temp_project_dir / "app.py"
    app.write_text(
        """
import main
import utils

def run():
    return main.main()
"""
    )

    return temp_project_dir


@pytest.fixture
def project_with_relative_imports(temp_project_dir: Path) -> Path:
    """Create a test project with relative imports causing circular dependencies."""
    # Create package structure
    pkg_dir = temp_project_dir / "myapp"
    pkg_dir.mkdir()

    # Create __init__.py
    (pkg_dir / "__init__.py").write_text("")

    # Create models.py
    (pkg_dir / "models.py").write_text(
        """
from . import views

class Model:
    pass
"""
    )

    # Create views.py (circular with relative import)
    (pkg_dir / "views.py").write_text(
        """
from .models import Model

class View:
    model = Model
"""
    )

    return temp_project_dir
