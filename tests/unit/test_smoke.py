# test_smoke.py — Smoke tests for the project skeleton
#
# These tests verify that the folder structure and package configuration are
# correct. They contain no application logic — their job is to catch broken
# imports and misconfigured packages before any real tests run.
#
# If these fail, the problem is in the project setup (missing __init__.py,
# wrong Python version, broken pyproject.toml) — not in application logic.


def test_app_package_is_importable() -> None:
    """The app package and all its subpackages must be importable.

    This test fails if:
    - A __init__.py file is missing from a subpackage folder
    - A module has a syntax error that prevents import
    - The Python path is not configured correctly
    """
    import app
    import app.api
    import app.audit
    import app.background
    import app.memory
    import app.redaction
    import app.routing
    import app.storage

    # If we get here without an ImportError, all packages are correctly structured
    assert app is not None


def test_python_version_is_311_or_higher() -> None:
    """Enforce the minimum Python version declared in pyproject.toml.

    This test fails if someone runs pytest with the wrong Python interpreter.
    It catches version drift before it causes hard-to-debug errors elsewhere.
    """
    import sys

    major, minor = sys.version_info.major, sys.version_info.minor
    assert (major, minor) >= (3, 11), (
        f"GateThread requires Python 3.11+. "
        f"You are running Python {major}.{minor}. "
        f"Check your virtual environment or pyenv configuration."
    )
