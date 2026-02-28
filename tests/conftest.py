"""
Pytest configuration for integration tests.

Provides a session-scoped fixture that ensures a Python virtual environment
exists with all required dependencies installed.
"""

import subprocess
import os
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def venv_python():
    """
    Session-scoped fixture that creates/reuses a virtual environment
    and installs requirements.txt. Returns the path to the venv's python3.
    """
    venv_dir = PROJECT_ROOT / "venv"
    python_path = venv_dir / "bin" / "python3"
    pip_path = venv_dir / "bin" / "pip"

    # Create venv if it doesn't exist
    if not python_path.exists():
        subprocess.run(
            ["python3", "-m", "venv", str(venv_dir)],
            check=True,
            cwd=str(PROJECT_ROOT),
        )

    # Install requirements
    requirements_file = PROJECT_ROOT / "requirements.txt"
    if requirements_file.exists():
        subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_file)],
            check=True,
            cwd=str(PROJECT_ROOT),
        )

    return str(python_path)
