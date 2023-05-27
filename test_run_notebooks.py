""" executes all Jupyter notebooks tracked by git """
# pylint: disable=wrong-import-position
# https://bugs.python.org/issue37373
import sys

if sys.platform == "win32" and sys.version_info[:2] >= (3, 7):
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import nbformat
import pytest
from git.cmd import Git
from nbconvert.preprocessors import ExecutePreprocessor


@pytest.fixture(
    params=(
        path
        for path in Git(Git(".").rev_parse("--show-toplevel")).ls_files().split("\n")
        if path.endswith(".ipynb")
    ),
    name="notebook_filename",
)
def _notebook_filename(request):
    return request.param


def test_run_notebooks(notebook_filename, tmp_path):
    """executes a given notebook"""
    with open(notebook_filename, encoding="utf8") as notebook_file:
        ExecutePreprocessor(timeout=15 * 60, kernel_name="python3").preprocess(
            nbformat.read(notebook_file, as_version=4), {"metadata": {"path": tmp_path}}
        )
