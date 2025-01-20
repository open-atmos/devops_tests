"""
test notebook_vars import is from open-atmos-jupyter-utils
"""

import pathlib

import pytest

from .utils import find_files


@pytest.fixture(
    params=find_files(file_extension=".py"),
    name="test_filename",
)
def _test_filename(request):
    return request.param


def test_notebook_vars_import(test_filename):
    """
    test notebook_vars import is from open-atmos-jupyter-utils
    """
    if pathlib.Path(test_filename).name in (
        "__init__.py",
        "test_tests_for_notebooks.py",
    ):
        return
    with open(test_filename, encoding="utf8") as f:
        if "from PySDM_examples.utils import notebook_vars" in f.read():
            raise AssertionError(
                f"notebook_vars imported from PySDM_examples.utils in {test_filename}.\n"
                f"Please use open-atmos-jupyter-utils package."
            )
