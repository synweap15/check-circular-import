"""Check Circular Import - A pre-commit hook for detecting circular imports."""

__version__ = "0.2.0"

from check_circular_import.detector import CircularImportDetector

__all__ = ["CircularImportDetector"]
