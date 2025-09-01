"""Test fixture with circular import - module B."""


def function_b():
    """Function that uses module A."""
    return "Result from B"
