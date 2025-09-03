# check-circular-import

[![CI](https://github.com/synweap15/check-circular-import/actions/workflows/ci.yml/badge.svg)](https://github.com/synweap15/check-circular-import/actions/workflows/ci.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A fast and reliable pre-commit hook for detecting circular imports in Python projects.

Supported Python versions: 3.9–3.12

## Features

- 🔍 Detects circular import dependencies in Python projects
- 🚀 Fast analysis using AST parsing
- 📦 Works as a pre-commit hook
- 🎯 Accurate detection of relative and absolute imports
- 📊 Detailed statistics and reporting
- 🔧 Configurable ignore patterns
- 📝 JSON output support for CI/CD integration

## Installation

### As a pre-commit hook

Add this to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/synweap15/check-circular-import
    rev: v0.2.0
    hooks:
      - id: check-circular-import
```

Then install the hook:

```bash
pre-commit install
```

### As a standalone tool

Using pip:

```bash
pip install check-circular-import
```

Using Poetry:

```bash
poetry add --dev check-circular-import
```

## Usage

### Command Line

```bash
# Check current directory
check-circular-import

# Check specific directory
check-circular-import /path/to/project

# Ignore specific directories
check-circular-import . --ignore tests docs

# Output as JSON
check-circular-import . --json

# Verbose output
check-circular-import . --verbose
```

### As a Pre-commit Hook

Once configured, the hook will run automatically on `git commit`:

```bash
git commit -m "Add new feature"
```

If circular imports are detected, the commit will be blocked and you'll see a detailed report.

### In CI/CD

You can use the tool in your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Check for circular imports
  run: |
    pip install check-circular-import
    check-circular-import .
```

## Example Output

```
============================================================
CIRCULAR IMPORT DETECTION REPORT
============================================================

Project root: /path/to/project

Statistics:
  - Total modules analyzed: 45
  - Total dependencies: 123
  - Modules with dependencies: 38
  - Circular dependencies found: 2

⚠️  Found 2 circular import(s):

Cycle 1:
  module_a
    ↓ imports
  module_b
    ↓ imports
  module_a (cycle completes)

Cycle 2:
  package.submodule_x
    ↓ imports
  package.submodule_y
    ↓ imports
  package.submodule_z
    ↓ imports
  package.submodule_x (cycle completes)

============================================================
```

## Configuration

### Ignore Patterns

By default, the following directories are ignored:
- `venv`, `env`, `.venv`
- `__pycache__`
- `.git`
- `node_modules`
- `.tox`
- `build`, `dist`
- `*.egg-info`

You can add additional ignore patterns:

```bash
check-circular-import . --ignore tests docs migrations
```

### Exit Codes

- `0`: No circular imports detected
- `1`: Circular imports found
- `2`: Error during execution

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/synweap15/check-circular-import.git
cd check-circular-import

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test
poetry run pytest tests/test_detector.py
```

### Testing with Tox (Recommended for Contributors)

Tox allows you to test across multiple Python versions locally, just like in CI:

```bash
# Install tox
poetry install --with dev

# Run tests across all Python versions
poetry run tox

# Run tests for specific Python version
poetry run tox -e py311

# Run only linting
poetry run tox -e lint

# Run only coverage
poetry run tox -e coverage

# Auto-format code
poetry run tox -e format

# Test pre-commit hooks
poetry run tox -e pre-commit

# Test as pre-commit hook
poetry run tox -e test-hook
```

**Available tox environments:**
- `py39`, `py310`, `py311`, `py312` - Test specific Python versions
- `lint` - Run Black, Ruff, and MyPy
- `format` - Auto-format code with Black and Ruff
- `coverage` - Generate coverage reports
- `pre-commit` - Run pre-commit hooks
- `test-hook` - Test the package as a pre-commit hook

### Code Quality

```bash
# Format code with Black
poetry run black .

# Lint with Ruff
poetry run ruff check .

# Type check with MyPy
poetry run mypy check_circular_import
```

### Running Pre-commit Hooks

```bash
# Run all hooks
poetry run pre-commit run --all-files

# Test the hook locally
poetry run pre-commit try-repo . check-circular-import --verbose --all-files
```

## How It Works

1. **File Discovery**: Recursively finds all Python files in the project
2. **AST Parsing**: Parses each file using Python's `ast` module
3. **Import Extraction**: Extracts all import statements (absolute and relative)
4. **Graph Building**: Constructs a dependency graph of all modules
5. **Cycle Detection**: Uses depth-first search (DFS) to find cycles
6. **Reporting**: Generates a clear report of all circular dependencies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Inspired by various circular import detection tools and the pre-commit framework.

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/synnweap15/check-circular-import/issues) on GitHub.
