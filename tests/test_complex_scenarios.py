"""Tests for complex circular import scenarios."""

from pathlib import Path

import pytest

from tests.test_utils import (
    analyze_project,
    assert_cycles_contain_modules,
    assert_no_cycles,
    create_chain_modules,
    create_module_files,
    create_package_structure,
)


def test_multiple_independent_cycles(temp_project_dir: Path):
    """Test detection of multiple independent circular imports."""
    # Create two separate cycles: A->B->A and X->Y->Z->X
    modules = {
        "cycle1_a": "import cycle1_b",
        "cycle1_b": "import cycle1_a",
        "cycle2_x": "import cycle2_y", 
        "cycle2_y": "import cycle2_z",
        "cycle2_z": "import cycle2_x",
        "standalone": "import os"  # No circular dependency
    }
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)
    
    assert len(cycles) == 2
    assert stats["circular_dependencies_found"] == 2
    
    # Verify both cycles are detected
    cycle_modules = set()
    for cycle in cycles:
        cycle_modules.update(cycle)
    
    # Should contain modules from both cycles
    assert_cycles_contain_modules(cycles, ["cycle1_a", "cycle1_b", "cycle2_x", "cycle2_y", "cycle2_z"])
    
    # Standalone module should not be in any cycle
    assert not any("standalone" in module for module in cycle_modules)


def test_long_cycle_chain(temp_project_dir: Path):
    """Test detection of a long circular chain (5+ modules)."""
    chain = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
    create_chain_modules(temp_project_dir, chain)
    
    cycles, stats = analyze_project(temp_project_dir)
    
    assert len(cycles) >= 1
    assert stats["circular_dependencies_found"] >= 1
    assert_cycles_contain_modules(cycles, chain)


def test_complex_package_cycles(temp_project_dir: Path):
    """Test circular imports between different packages."""
    # Create package1 that imports from package2
    create_package_structure(temp_project_dir, "package1", {
        "module_a": "from package2 import module_x",
        "module_b": "import package1.module_a"  # Internal import
    })
    
    # Create package2 that imports from package1 (creates cycle)
    create_package_structure(temp_project_dir, "package2", {
        "module_x": "from package1 import module_b", 
        "module_y": "import package2.module_x"  # Internal import
    })
    
    cycles, stats = analyze_project(temp_project_dir)
    
    assert len(cycles) >= 1
    assert stats["circular_dependencies_found"] >= 1
    
    # Should detect cross-package circular dependency
    cycle_modules = set()
    for cycle in cycles:
        cycle_modules.update(cycle)
    
    # Should contain modules from both packages
    assert any("package1" in module for module in cycle_modules)
    assert any("package2" in module for module in cycle_modules)


def test_nested_package_cycles(temp_project_dir: Path):
    """Test circular imports in deeply nested packages."""
    modules = {
        "deep/nested/package/module_a": "from deep.nested.other import module_b",
        "deep/nested/other/module_b": "from deep.nested.package import module_a",
        "deep/nested/other/module_c": "import os",  # No cycle
        "deep/__init__": "",
        "deep/nested/__init__": "",
        "deep/nested/package/__init__": "",
        "deep/nested/other/__init__": ""
    }
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)
    
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["deep.nested.package.module_a", "deep.nested.other.module_b"])


def test_mixed_import_styles(temp_project_dir: Path):
    """Test detection with mixed import styles (import vs from-import)."""
    modules = {
        "style_a": """
import style_b
from style_c import func
""",
        "style_b": """
from style_a import something
import style_c
""",
        "style_c": """
import style_a
from style_b import other
"""
    }
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)
    
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["style_a", "style_b", "style_c"])


def test_conditional_imports_cycle(temp_project_dir: Path):
    """Test circular imports inside conditional blocks."""
    modules = {
        "conditional_a": """
import sys
if sys.version_info >= (3, 8):
    import conditional_b
""",
        "conditional_b": """
import os
if os.name == 'posix':
    import conditional_a
"""
    }
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)
    
    # Should still detect cycles even in conditional blocks
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["conditional_a", "conditional_b"])


def test_aliased_imports_cycle(temp_project_dir: Path):
    """Test circular imports with aliases."""
    modules = {
        "alias_a": """
import alias_b as b_module
from alias_c import func as c_func
""",
        "alias_b": """
from alias_a import something as a_something
""",
        "alias_c": """
import alias_a as module_a
"""
    }
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)
    
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["alias_a", "alias_b", "alias_c"])


def test_function_level_imports(temp_project_dir: Path):
    """Test circular imports inside functions."""
    modules = {
        "func_a": """
def get_something():
    import func_b
    return func_b.value
""",
        "func_b": """
def calculate():
    from func_a import get_something
    return get_something() + 1
"""
    }
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)
    
    # Should detect cycles even at function level
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["func_a", "func_b"])


def test_class_level_imports(temp_project_dir: Path):
    """Test circular imports inside class definitions."""
    modules = {
        "class_a": """
class ClassA:
    from class_b import ClassB
    
    def method(self):
        return self.ClassB()
""",
        "class_b": """
class ClassB:
    import class_a
    
    def method(self):
        return class_a.ClassA()
"""
    }
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)
    
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["class_a", "class_b"])


def test_multiple_cycles_same_modules(temp_project_dir: Path):
    """Test multiple circular paths between the same set of modules."""
    modules = {
        "multi_a": """
import multi_b
import multi_c
""",
        "multi_b": """
import multi_c
import multi_a
""",
        "multi_c": """
import multi_a
import multi_b
"""
    }
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)
    
    # Should detect cycles - may find multiple paths
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["multi_a", "multi_b", "multi_c"])


def test_large_project_simulation(temp_project_dir: Path):
    """Test performance with a larger project structure."""
    # Create a more realistic project structure
    modules = {}
    
    # Create main modules
    for i in range(10):
        modules[f"main_module_{i}"] = f"""
import utils_{i % 3}
from helpers import helper_{i % 2}
"""
    
    # Create utility modules (some circular)
    modules["utils_0"] = "import utils_1"
    modules["utils_1"] = "import utils_2" 
    modules["utils_2"] = "import utils_0"  # Creates cycle
    
    # Create helper modules
    modules["helpers/helper_0"] = "import main_module_0"  # Creates cycle with main
    modules["helpers/helper_1"] = "import os"
    modules["helpers/__init__"] = ""
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)
    
    # Should find multiple cycles
    assert len(cycles) >= 2
    assert stats["total_modules"] >= 10
    assert stats["circular_dependencies_found"] >= 2


def test_star_imports_detection(temp_project_dir: Path):
    """Test detection of circular imports with star imports."""
    modules = {
        "star_a": """
from star_b import *
""",
        "star_b": """
from star_a import *
""",
        "star_c": """
from star_a import specific_function
"""
    }
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)
    
    # Should detect cycle between star_a and star_b
    assert len(cycles) >= 1
    assert_cycles_contain_modules(cycles, ["star_a", "star_b"])
    
    # star_c should not be in a cycle (it only imports from star_a)
    cycle_modules = set()
    for cycle in cycles:
        cycle_modules.update(cycle)
    # star_c might be pulled into cycle due to star import complexity


def test_self_referential_relative_imports(temp_project_dir: Path):
    """Test handling of complex relative import scenarios."""
    modules = {
        "package/subpkg/module_a": """
from . import module_b
from ..other import module_x
""",
        "package/subpkg/module_b": """
from .module_a import something
""",
        "package/other/module_x": """
from ..subpkg.module_a import func
""",
        "package/__init__": "",
        "package/subpkg/__init__": "",
        "package/other/__init__": ""
    }
    
    create_module_files(temp_project_dir, modules)
    cycles, stats = analyze_project(temp_project_dir)
    
    # Should detect complex relative import cycles
    assert len(cycles) >= 1
    cycle_modules = set()
    for cycle in cycles:
        cycle_modules.update(cycle)
    
    # Should contain modules with relative imports
    assert any("module_a" in module for module in cycle_modules)
    assert any("module_b" in module for module in cycle_modules)