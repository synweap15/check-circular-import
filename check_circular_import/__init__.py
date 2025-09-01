"""Check Circular Import - A pre-commit hook for detecting circular imports."""

__version__ = "0.1.0"

from check_circular_import.detector import CircularImportDetector

__all__ = ["CircularImportDetector"]
