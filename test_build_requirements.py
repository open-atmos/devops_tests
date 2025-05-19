"""checks requirements consistency between PySDM and PySDM examples"""

import tomllib
from pathlib import Path

from .utils import repo_path


def test_build_requirements_with_examples():
    """tests if build requirements in PySDM and PySDM examples matches"""
    with open(Path(repo_path(), "pyproject.toml"), "rb") as proj_f:
        with open(Path(repo_path(), "examples/pyproject.toml"), "rb") as examples_f:
            assert (
                tomllib.load(proj_f)["build-system"]["requires"]
                == tomllib.load(examples_f)["build-system"]["requires"]
            )
