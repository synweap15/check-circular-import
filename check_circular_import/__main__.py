"""Command-line interface for check-circular-import."""

import argparse
import json
import sys
from pathlib import Path

from check_circular_import import __version__
from check_circular_import.detector import CircularImportDetector
from check_circular_import.utils import format_cycle_output


def print_report(
    cycles: list[list[str]], stats: dict, root_directory: Path, json_output: bool
) -> None:
    """Print a formatted report of the analysis."""
    if json_output:
        result = {
            "root_directory": str(root_directory),
            "statistics": stats,
            "cycles": cycles,
        }
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 60)
        print("CIRCULAR IMPORT DETECTION REPORT")
        print("=" * 60)

        print(f"\nProject root: {root_directory}")
        print("\nStatistics:")
        print(f"  - Total modules analyzed: {stats['total_modules']}")
        print(f"  - Total dependencies: {stats['total_dependencies']}")
        print(f"  - Modules with dependencies: {stats['modules_with_dependencies']}")
        print(
            f"  - Circular dependencies found: {stats['circular_dependencies_found']}"
        )

        if cycles:
            print(f"\n⚠️  Found {len(cycles)} circular import(s):\n")

            for i, cycle in enumerate(cycles, 1):
                print(f"Cycle {i}:")
                print(format_cycle_output(cycle))
                print()
        else:
            print("\n✅ No circular imports detected!")

        print("=" * 60)


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Detect circular imports in Python projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  check-circular-import .
  check-circular-import /path/to/project
  check-circular-import . --ignore tests docs
  check-circular-import . --json > report.json
        """,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to analyze (default: current directory)",
    )

    parser.add_argument(
        "--ignore",
        nargs="*",
        default=None,
        help="Additional directories to ignore (beyond defaults)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed progress information",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show version and exit",
    )

    args = parser.parse_args()

    # Create detector and run analysis
    try:
        detector = CircularImportDetector(args.directory, args.ignore)

        if args.verbose and not args.json:
            print(f"Analyzing Python files in: {Path(args.directory).resolve()}")
            print(f"Ignoring directories: {', '.join(detector.ignore_dirs)}")
            print()
        cycles, stats = detector.analyze()

        print_report(cycles, stats, detector.root_directory, args.json)

        # Exit with error code if cycles were found
        return 1 if cycles else 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
