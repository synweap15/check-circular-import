"""Test fixture with circular import - module A."""

from tests.fixtures import circular_b


def function_a():
    """Function that uses module B."""
    return circular_b.function_b()
